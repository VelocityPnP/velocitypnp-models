#!/usr/bin/env python3
"""Build and verify deterministic VelocityPnP model packages."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Any


PACKAGE_SCHEMA_VERSION = 1
REQUIRED_FILES = {"best.onnx", "best.pt", "model-manifest.json"}
REQUIRED_PACKAGE_FILES = REQUIRED_FILES | {"LICENSE", "model-card.md"}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def selected_files(source: Path) -> list[Path]:
    if not source.is_dir():
        raise ValueError(f"model output directory does not exist: {source}")
    files = sorted(
        path
        for path in source.iterdir()
        if path.is_file()
        and (path.name in REQUIRED_FILES or path.suffix == ".json")
    )
    names = {path.name for path in files}
    missing = sorted(REQUIRED_FILES - names)
    if missing:
        raise ValueError(f"model output is missing: {', '.join(missing)}")
    return files


def load_manifest(source: Path) -> tuple[dict[str, Any], bytes]:
    manifest_bytes = (source / "model-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    for artifact_name in ("checkpoint", "onnx"):
        artifact = manifest.get("artifacts", {}).get(artifact_name)
        if not isinstance(artifact, dict):
            raise ValueError(f"manifest has no {artifact_name} artifact")
        artifact_path = artifact.get("path")
        if not isinstance(artifact_path, str) or Path(artifact_path).name != artifact_path:
            raise ValueError(f"manifest {artifact_name} path is unsafe")
        path = source / artifact_path
        if not path.is_file():
            raise ValueError(f"manifest artifact does not exist: {artifact_path}")
        if path.stat().st_size != artifact.get("size_bytes"):
            raise ValueError(f"manifest size does not match: {artifact_path}")
        if sha256_file(path) != artifact.get("sha256"):
            raise ValueError(f"manifest checksum does not match: {artifact_path}")
    return manifest, manifest_bytes


def archive_member(name: str, data: bytes) -> tuple[tarfile.TarInfo, bytes]:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info, data


def build_package(
    family: str,
    version: str,
    release_tag: str,
    source: Path,
    output_dir: Path,
    license_file: Path,
    model_card: Path,
) -> dict[str, Any]:
    if not family or "/" in family or not version or "/" in version:
        raise ValueError("family and version must be non-empty path segments")
    manifest, manifest_bytes = load_manifest(source)
    package_name = f"{family}-{version}"
    payloads = {path.name: path.read_bytes() for path in selected_files(source)}
    if not license_file.is_file():
        raise ValueError(f"license does not exist: {license_file}")
    if not model_card.is_file():
        raise ValueError(f"model card does not exist: {model_card}")
    payloads["LICENSE"] = license_file.read_bytes()
    payloads["model-card.md"] = model_card.read_bytes()
    inventory = [
        {"path": name, "sha256": sha256_bytes(data), "size_bytes": len(data)}
        for name, data in sorted(payloads.items())
    ]
    metadata = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "id": f"{family}/{version}",
        "family": family,
        "version": version,
        "release_tag": release_tag,
        "contract_version": manifest.get("contract_version"),
        "license": manifest.get("license"),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "files": inventory,
    }
    metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    payloads["package-metadata.json"] = metadata_bytes

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{package_name}.tar.gz"
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(
                fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT
            ) as archive:
                for name, data in sorted(payloads.items()):
                    info, content = archive_member(f"{package_name}/{name}", data)
                    archive.addfile(info, io.BytesIO(content))

    return {
        "id": metadata["id"],
        "path": str(output),
        "name": output.name,
        "sha256": sha256_file(output),
        "size_bytes": output.stat().st_size,
        "manifest_sha256": metadata["manifest_sha256"],
    }


def verify_package(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    actual_archive_sha256 = sha256_file(path)
    if expected_sha256 is not None and actual_archive_sha256 != expected_sha256:
        raise ValueError("package checksum does not match")
    payloads: dict[str, bytes] = {}
    roots: set[str] = set()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if not member.isfile() or len(pure.parts) != 2:
                raise ValueError(f"unsafe package member: {member.name}")
            root, name = pure.parts
            if name in payloads:
                raise ValueError(f"duplicate package member: {name}")
            roots.add(root)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read package member: {member.name}")
            payloads[name] = stream.read()
    if len(roots) != 1:
        raise ValueError("package must have one top-level directory")
    if "package-metadata.json" not in payloads:
        raise ValueError("package has no package metadata")
    metadata = json.loads(payloads.pop("package-metadata.json"))
    if metadata.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise ValueError("unsupported package schema")
    missing = sorted(REQUIRED_PACKAGE_FILES - set(payloads))
    if missing:
        raise ValueError(f"package is missing: {', '.join(missing)}")
    expected_files = {
        item["path"]: (item["sha256"], item["size_bytes"])
        for item in metadata.get("files", [])
    }
    if set(payloads) != set(expected_files):
        raise ValueError("package inventory does not match its files")
    for name, data in payloads.items():
        if expected_files[name] != (sha256_bytes(data), len(data)):
            raise ValueError(f"package file checksum does not match: {name}")
    manifest_bytes = payloads.get("model-manifest.json")
    if manifest_bytes is None:
        raise ValueError("package has no model manifest")
    if sha256_bytes(manifest_bytes) != metadata.get("manifest_sha256"):
        raise ValueError("model manifest checksum does not match")
    manifest = json.loads(manifest_bytes)
    for artifact_name in ("checkpoint", "onnx"):
        artifact = manifest["artifacts"][artifact_name]
        data = payloads.get(artifact["path"])
        if data is None:
            raise ValueError(f"package has no {artifact_name} artifact")
        if len(data) != artifact["size_bytes"]:
            raise ValueError(f"package {artifact_name} size does not match")
        if sha256_bytes(data) != artifact["sha256"]:
            raise ValueError(f"package {artifact_name} checksum does not match")
    return {
        "id": metadata["id"],
        "sha256": actual_archive_sha256,
        "size_bytes": path.stat().st_size,
        "file_count": len(payloads),
        "contract_version": metadata["contract_version"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("family")
    build.add_argument("version")
    build.add_argument("release_tag")
    build.add_argument("source", type=Path)
    build.add_argument("--output-dir", type=Path, default=Path("dist"))
    build.add_argument(
        "--license-file", type=Path, default=REPOSITORY_ROOT / "LICENSE"
    )
    build.add_argument("--model-card", type=Path, required=True)
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
            args.output_dir,
            args.license_file,
            args.model_card,
        )
    else:
        result = verify_package(args.package, args.sha256)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
