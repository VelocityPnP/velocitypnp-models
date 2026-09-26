#!/usr/bin/env python3
"""Build and verify deterministic VelocityPnP dataset packages."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Any, BinaryIO


PACKAGE_SCHEMA_VERSION = 1
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRECTORIES = {".git", "__pycache__", "training"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(value: str, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ValueError(f"{field} must be a safe relative path")
    return path


def selected_tree_files(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError(f"dataset directory does not exist: {root}")
    files = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def dataset_image_paths(manifest: dict[str, Any]) -> list[PurePosixPath]:
    samples = manifest.get("samples")
    if not isinstance(samples, list):
        raise ValueError("ground-truth manifest has no sample list")
    paths = []
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError("ground-truth sample must be an object")
        if sample.get("included") is not True:
            continue
        if "bare_image_path" in sample or "observed_image_path" in sample:
            fields = ("bare_image_path", "observed_image_path")
        else:
            fields = ("image_path",)
        for field in fields:
            value = sample.get(field)
            if not isinstance(value, str):
                raise ValueError(f"included sample has no {field}")
            paths.append(safe_relative_path(value, field))
    return paths


def dataset_summary(
    root: Path, manifest_relative: PurePosixPath
) -> dict[str, Any]:
    manifest_path = root.joinpath(*manifest_relative.parts)
    if not manifest_path.is_file():
        raise ValueError(f"ground-truth manifest does not exist: {manifest_path}")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    logical_root = manifest_path.parent
    digest = hashlib.sha256()
    digest.update(manifest_relative.name.encode())
    digest.update(b"\0")
    digest.update(bytes.fromhex(sha256_bytes(manifest_bytes)))
    for relative in dataset_image_paths(manifest):
        image = logical_root.joinpath(*relative.parts)
        resolved = image.resolve()
        if not resolved.is_relative_to(logical_root.resolve()) or not image.is_file():
            raise ValueError(f"dataset image does not exist: {relative}")
        digest.update(relative.as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(image)))

    samples = manifest["samples"]
    included = [sample for sample in samples if sample.get("included") is True]
    split_counts: dict[str, int] = {}
    for sample in included:
        split = sample.get("split")
        if not isinstance(split, str) or not split:
            raise ValueError("included sample has no split")
        split_counts[split] = split_counts.get(split, 0) + 1
    classes = manifest.get("classes")
    if not isinstance(classes, list) or not all(
        isinstance(name, str) for name in classes
    ):
        raise ValueError("ground-truth manifest has invalid classes")
    return {
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "content_sha256": digest.hexdigest(),
        "sample_count": len(samples),
        "included_sample_count": len(included),
        "split_counts": dict(sorted(split_counts.items())),
        "classes": classes,
    }


def archive_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    archive.addfile(archive_info(name, len(data)), io.BytesIO(data))


def add_file(
    archive: tarfile.TarFile, name: str, path: Path, stream: BinaryIO
) -> None:
    archive.addfile(archive_info(name, path.stat().st_size), stream)


def parse_audit_roots(values: list[str]) -> list[tuple[str, Path]]:
    roots = []
    names = set()
    for value in values:
        name, separator, raw_path = value.partition("=")
        if not separator or not raw_path:
            raise ValueError("audit roots must use NAME=PATH")
        safe_relative_path(name, "audit root name")
        if "/" in name or name in names:
            raise ValueError(f"invalid or repeated audit root name: {name}")
        names.add(name)
        roots.append((name, Path(raw_path)))
    return roots


def build_package(
    family: str,
    version: str,
    release_tag: str,
    source: Path,
    manifest_relative: str,
    output_dir: Path,
    license_file: Path,
    dataset_card: Path,
    audit_roots: list[tuple[str, Path]],
) -> dict[str, Any]:
    if not family or "/" in family or not version or "/" in version:
        raise ValueError("family and version must be non-empty path segments")
    if not release_tag:
        raise ValueError("release tag is required")
    source = source.resolve()
    manifest_path = safe_relative_path(manifest_relative, "manifest path")
    summary = dataset_summary(source, manifest_path)
    if not license_file.is_file():
        raise ValueError(f"license does not exist: {license_file}")
    if not dataset_card.is_file():
        raise ValueError(f"dataset card does not exist: {dataset_card}")

    payloads: dict[str, Path] = {
        f"data/{path.relative_to(source).as_posix()}": path
        for path in selected_tree_files(source)
    }
    for name, audit_root in audit_roots:
        audit_root = audit_root.resolve()
        for path in selected_tree_files(audit_root):
            archive_path = f"audit/{name}/{path.relative_to(audit_root).as_posix()}"
            if archive_path in payloads:
                raise ValueError(f"duplicate package path: {archive_path}")
            payloads[archive_path] = path

    package_name = f"{family}-{version}"
    fixed_payloads = {
        "LICENSE": license_file,
        "dataset-card.md": dataset_card,
    }
    for name, path in fixed_payloads.items():
        if name in payloads:
            raise ValueError(f"duplicate package path: {name}")
        payloads[name] = path
    inventory = [
        {
            "path": name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for name, path in sorted(payloads.items())
    ]
    metadata = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "id": f"{family}/{version}",
        "family": family,
        "version": version,
        "release_tag": release_tag,
        "manifest_path": f"data/{manifest_path.as_posix()}",
        **summary,
        "files": inventory,
    }
    metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{package_name}.tar.gz"
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(
                fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
            ) as archive:
                add_bytes(
                    archive,
                    f"{package_name}/dataset-metadata.json",
                    metadata_bytes,
                )
                for name, path in sorted(payloads.items()):
                    with path.open("rb") as stream:
                        add_file(archive, f"{package_name}/{name}", path, stream)

    return {
        "id": metadata["id"],
        "path": str(output),
        "name": output.name,
        "sha256": sha256_file(output),
        "size_bytes": output.stat().st_size,
        **summary,
    }


def archive_members(path: Path) -> tuple[str, dict[str, tuple[str, int]], bytes]:
    roots = set()
    inventory: dict[str, tuple[str, int]] = {}
    metadata_bytes = None
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if (
                not member.isfile()
                or pure.is_absolute()
                or len(pure.parts) < 2
                or any(part in {"", ".", ".."} for part in pure.parts)
            ):
                raise ValueError(f"unsafe package member: {member.name}")
            root = pure.parts[0]
            relative = PurePosixPath(*pure.parts[1:]).as_posix()
            if relative in inventory:
                raise ValueError(f"duplicate package member: {relative}")
            roots.add(root)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read package member: {member.name}")
            digest = hashlib.sha256()
            size = 0
            retained = bytearray() if relative == "dataset-metadata.json" else None
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
                if retained is not None:
                    retained.extend(block)
            inventory[relative] = (digest.hexdigest(), size)
            if retained is not None:
                metadata_bytes = bytes(retained)
    if len(roots) != 1:
        raise ValueError("package must have one top-level directory")
    if metadata_bytes is None:
        raise ValueError("package has no dataset metadata")
    return roots.pop(), inventory, metadata_bytes


def verify_package(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    archive_sha256 = sha256_file(path)
    if expected_sha256 is not None and archive_sha256 != expected_sha256:
        raise ValueError("package checksum does not match")
    root, actual_files, metadata_bytes = archive_members(path)
    metadata = json.loads(metadata_bytes)
    if metadata.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise ValueError("unsupported package schema")
    if root != f"{metadata.get('family')}-{metadata.get('version')}":
        raise ValueError("package directory does not match its identity")
    if metadata.get("id") != f"{metadata.get('family')}/{metadata.get('version')}":
        raise ValueError("package ID does not match its identity")

    expected_files = {
        item["path"]: (item["sha256"], item["size_bytes"])
        for item in metadata.get("files", [])
    }
    actual_files.pop("dataset-metadata.json", None)
    if actual_files != expected_files:
        raise ValueError("dataset package inventory does not match its files")
    for required in ("LICENSE", "dataset-card.md"):
        if required not in actual_files:
            raise ValueError(f"dataset package has no {required}")

    manifest_archive_path = metadata.get("manifest_path")
    if not isinstance(manifest_archive_path, str):
        raise ValueError("dataset package has no manifest path")
    manifest_expected = actual_files.get(manifest_archive_path)
    if manifest_expected is None:
        raise ValueError("dataset package has no ground-truth manifest")
    if manifest_expected[0] != metadata.get("manifest_sha256"):
        raise ValueError("ground-truth manifest checksum does not match")

    with tarfile.open(path, "r:gz") as archive:
        member = archive.getmember(f"{root}/{manifest_archive_path}")
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError("cannot read ground-truth manifest")
        manifest = json.load(stream)
    manifest_parent = PurePosixPath(manifest_archive_path).parent
    logical_manifest_name = PurePosixPath(manifest_archive_path).name
    digest = hashlib.sha256()
    digest.update(logical_manifest_name.encode())
    digest.update(b"\0")
    digest.update(bytes.fromhex(manifest_expected[0]))
    for relative in dataset_image_paths(manifest):
        archive_image = (manifest_parent / relative).as_posix()
        image = actual_files.get(archive_image)
        if image is None:
            raise ValueError(f"dataset package has no image: {relative}")
        digest.update(relative.as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(image[0]))
    if digest.hexdigest() != metadata.get("content_sha256"):
        raise ValueError("dataset content checksum does not match")

    return {
        "id": metadata["id"],
        "sha256": archive_sha256,
        "size_bytes": path.stat().st_size,
        "file_count": len(actual_files),
        "manifest_sha256": metadata["manifest_sha256"],
        "content_sha256": metadata["content_sha256"],
        "sample_count": metadata["sample_count"],
        "included_sample_count": metadata["included_sample_count"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("family")
    build.add_argument("version")
    build.add_argument("release_tag")
    build.add_argument("source", type=Path)
    build.add_argument(
        "--manifest", default="manifest.ground-truth.json"
    )
    build.add_argument("--output-dir", type=Path, default=Path("dist"))
    build.add_argument(
        "--license-file", type=Path, default=REPOSITORY_ROOT / "LICENSE"
    )
    build.add_argument("--dataset-card", type=Path, required=True)
    build.add_argument("--audit-root", action="append", default=[])
    verify = commands.add_parser("verify")
    verify.add_argument("package", type=Path)
    verify.add_argument("--sha256")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "build":
        result = build_package(
            args.family,
            args.version,
            args.release_tag,
            args.source,
            args.manifest,
            args.output_dir,
            args.license_file,
            args.dataset_card,
            parse_audit_roots(args.audit_root),
        )
    else:
        result = verify_package(args.package, args.sha256)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
