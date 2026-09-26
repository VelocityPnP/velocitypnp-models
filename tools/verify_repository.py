#!/usr/bin/env python3
"""Validate the checked-in VelocityPnP model catalog."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
STATES = {"candidate", "validated", "approved", "retired"}
AVAILABILITY = {"local", "published"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe_relative_file(value: object, field: str) -> Path:
    require(isinstance(value, str), f"{field} must be a string")
    pure = PurePosixPath(value)
    require(
        not pure.is_absolute() and all(part not in {"", ".", ".."} for part in pure.parts),
        f"{field} must be a safe relative path",
    )
    path = ROOT.joinpath(*pure.parts)
    require(path.is_file(), f"{field} does not exist: {value}")
    return path


def validate_asset(asset: object, entry: dict, kind: str) -> None:
    require(isinstance(asset, dict), "asset is required")
    require(isinstance(asset.get("name"), str) and asset["name"].endswith(".tar.gz"),
            "asset name must be a tar.gz file")
    require(isinstance(asset.get("sha256"), str) and SHA256.fullmatch(asset["sha256"]),
            "asset checksum is invalid")
    require(isinstance(asset.get("size_bytes"), int) and asset["size_bytes"] > 0,
            "asset size is invalid")
    require(asset.get("availability") in AVAILABILITY, "asset availability is invalid")
    if asset["availability"] == "published":
        expected_url = (
            "https://github.com/VelocityPnP/velocitypnp-models/releases/download/"
            f"{entry['release_tag']}/{asset['name']}"
        )
        require(asset.get("download_url") == expected_url,
                f"published {kind} asset has an unexpected download URL")
    else:
        require(asset.get("download_url") is None,
                f"local {kind} asset must not have a download URL")


def validate_dataset_entry(entry: object) -> None:
    require(isinstance(entry, dict), "dataset entries must be objects")
    family = entry.get("family")
    version = entry.get("version")
    require(isinstance(family, str) and family, "dataset family is required")
    require(isinstance(version, str) and version, "dataset version is required")
    require(entry.get("id") == f"{family}/{version}", "dataset ID does not match")
    require(isinstance(entry.get("release_tag"), str), "dataset release tag is required")
    for field in ("manifest_sha256", "content_sha256"):
        require(isinstance(entry.get(field), str) and SHA256.fullmatch(entry[field]),
                f"{entry.get('id')} has invalid {field}")
    sample_count = entry.get("sample_count")
    included_count = entry.get("included_sample_count")
    require(isinstance(sample_count, int) and sample_count > 0,
            "dataset sample count is invalid")
    require(isinstance(included_count, int) and 0 < included_count <= sample_count,
            "dataset included sample count is invalid")
    split_counts = entry.get("split_counts")
    require(isinstance(split_counts, dict) and split_counts,
            "dataset split counts are required")
    require(all(isinstance(name, str) and isinstance(count, int) and count >= 0
                for name, count in split_counts.items()),
            "dataset split counts are invalid")
    require(sum(split_counts.values()) == included_count,
            "dataset split counts do not match included samples")
    classes = entry.get("classes")
    require(isinstance(classes, list)
            and all(isinstance(name, str) for name in classes),
            "dataset classes are invalid")
    validate_asset(entry.get("asset"), entry, "dataset")
    safe_relative_file(entry.get("dataset_card"), "dataset_card")


def load_dataset_catalog() -> dict[str, dict]:
    catalog = json.loads((ROOT / "datasets.json").read_text())
    require(catalog.get("schema_version") == 1,
            "unsupported dataset catalog schema")
    datasets = catalog.get("datasets")
    require(isinstance(datasets, list), "catalog datasets must be a list")
    by_id = {}
    assets = set()
    for entry in datasets:
        validate_dataset_entry(entry)
        require(entry["id"] not in by_id, f"duplicate dataset ID: {entry['id']}")
        require(entry["asset"]["name"] not in assets,
                f"duplicate dataset asset: {entry['asset']['name']}")
        by_id[entry["id"]] = entry
        assets.add(entry["asset"]["name"])
    return by_id


def validate_entry(entry: object, datasets: dict[str, dict]) -> None:
    require(isinstance(entry, dict), "catalog entries must be objects")
    family = entry.get("family")
    version = entry.get("version")
    require(isinstance(family, str) and family, "family is required")
    require(isinstance(version, str) and version, "version is required")
    require(entry.get("id") == f"{family}/{version}", "model ID does not match")
    require(entry.get("status") in STATES, "model status is invalid")
    require(isinstance(entry.get("contract_version"), str), "contract is required")
    require(isinstance(entry.get("release_tag"), str), "release tag is required")
    for field in (
        "manifest_sha256",
        "onnx_sha256",
        "checkpoint_sha256",
        "dataset_content_sha256",
    ):
        require(isinstance(entry.get(field), str) and SHA256.fullmatch(entry[field]),
                f"{entry.get('id')} has invalid {field}")
    source = entry.get("source")
    require(isinstance(source, dict), "source provenance is required")
    require(isinstance(source.get("git_commit"), str)
            and GIT_COMMIT.fullmatch(source["git_commit"]),
            f"{entry.get('id')} has an invalid source commit")
    require(isinstance(source.get("dirty"), bool), "source dirty flag is required")
    require(isinstance(source.get("training_source_sha256"), str)
            and SHA256.fullmatch(source["training_source_sha256"]),
            f"{entry.get('id')} has an invalid training source digest")
    validate_asset(entry.get("asset"), entry, "model")
    dataset_id = entry.get("dataset")
    require(isinstance(dataset_id, str) and dataset_id in datasets,
            f"{entry.get('id')} references an unknown dataset")
    require(datasets[dataset_id]["content_sha256"]
            == entry.get("dataset_content_sha256"),
            f"{entry.get('id')} dataset digest does not match its dataset")
    safe_relative_file(entry.get("model_card"), "model_card")


def validate_catalog() -> dict[str, int]:
    datasets = load_dataset_catalog()
    catalog = json.loads((ROOT / "catalog.json").read_text())
    require(catalog.get("schema_version") == 1, "unsupported catalog schema")
    models = catalog.get("models")
    require(isinstance(models, list), "catalog models must be a list")
    ids: set[str] = set()
    assets: set[str] = set()
    for entry in models:
        validate_entry(entry, datasets)
        require(entry["id"] not in ids, f"duplicate model ID: {entry['id']}")
        require(entry["asset"]["name"] not in assets,
                f"duplicate asset name: {entry['asset']['name']}")
        ids.add(entry["id"])
        assets.add(entry["asset"]["name"])
    return {
        "model_count": len(models),
        "model_asset_count": len(assets),
        "dataset_count": len(datasets),
    }


if __name__ == "__main__":
    print(json.dumps(validate_catalog(), indent=2, sort_keys=True))
