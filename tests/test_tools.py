from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.model_package import build_package, sha256_bytes, verify_package
from tools.dataset_package import (
    build_package as build_dataset_package,
    verify_package as verify_dataset_package,
)


class PackageTests(unittest.TestCase):
    def make_model(self, root: Path) -> Path:
        source = root / "source"
        source.mkdir()
        checkpoint = b"checkpoint"
        onnx = b"onnx"
        (source / "best.pt").write_bytes(checkpoint)
        (source / "best.onnx").write_bytes(onnx)
        manifest = {
            "contract_version": "velocitypnp.test.v1",
            "license": {"artifact": "Apache-2.0"},
            "artifacts": {
                "checkpoint": {
                    "path": "best.pt",
                    "sha256": sha256_bytes(checkpoint),
                    "size_bytes": len(checkpoint),
                },
                "onnx": {
                    "path": "best.onnx",
                    "sha256": sha256_bytes(onnx),
                    "size_bytes": len(onnx),
                },
            },
        }
        (source / "model-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        (source / "evaluation-records.json").write_text("[]\n")
        return source

    def package_documents(self, root: Path) -> tuple[Path, Path]:
        license_file = root / "LICENSE"
        model_card = root / "model-card.md"
        license_file.write_text("Apache-2.0 test license\n")
        model_card.write_text("# Test model\n")
        return license_file, model_card

    def test_build_is_repeatable_and_verifies(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_model(root)
            license_file, model_card = self.package_documents(root)
            first = build_package(
                "test",
                "1",
                "models-1",
                source,
                root / "one",
                license_file,
                model_card,
            )
            second = build_package(
                "test",
                "1",
                "models-1",
                source,
                root / "two",
                license_file,
                model_card,
            )
            self.assertEqual(first["sha256"], second["sha256"])
            result = verify_package(Path(first["path"]), first["sha256"])
            self.assertEqual(result["id"], "test/1")
            self.assertEqual(result["file_count"], 6)

    def test_wrong_archive_checksum_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_model(root)
            license_file, model_card = self.package_documents(root)
            built = build_package(
                "test",
                "1",
                "models-1",
                source,
                root / "dist",
                license_file,
                model_card,
            )
            with self.assertRaisesRegex(ValueError, "package checksum"):
                verify_package(Path(built["path"]), "0" * 64)

    def test_manifest_artifact_mismatch_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_model(root)
            license_file, model_card = self.package_documents(root)
            (source / "best.onnx").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "manifest size"):
                build_package(
                    "test",
                    "1",
                    "models-1",
                    source,
                    root / "dist",
                    license_file,
                    model_card,
                )


class DatasetPackageTests(unittest.TestCase):
    def make_dataset(self, root: Path) -> Path:
        source = root / "dataset"
        (source / "images/train").mkdir(parents=True)
        (source / "images/eval").mkdir(parents=True)
        (source / "images/train/flat.png").write_bytes(b"flat")
        (source / "images/eval/empty.png").write_bytes(b"empty")
        (source / "images/eval/rejected.png").write_bytes(b"rejected")
        manifest = {
            "schema_version": 1,
            "classes": ["component_flat", "component_on_edge"],
            "samples": [
                {
                    "id": "flat",
                    "split": "train",
                    "included": True,
                    "class_name": "component_flat",
                    "image_path": "images/train/flat.png",
                },
                {
                    "id": "empty",
                    "split": "eval",
                    "included": True,
                    "class_name": None,
                    "image_path": "images/eval/empty.png",
                },
                {
                    "id": "rejected",
                    "split": "eval",
                    "included": False,
                    "class_name": None,
                    "image_path": "images/eval/rejected.png",
                },
            ],
        }
        (source / "manifest.ground-truth.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        (source / "review-decisions.json").write_text('{"reviewed": true}\n')
        training = source / "training/run"
        training.mkdir(parents=True)
        (training / "best.pt").write_bytes(b"not dataset content")
        return source

    def make_documents(self, root: Path) -> tuple[Path, Path]:
        license_file = root / "LICENSE"
        dataset_card = root / "dataset-card.md"
        license_file.write_text("Apache-2.0 test license\n")
        dataset_card.write_text("# Test dataset\n")
        return license_file, dataset_card

    def test_build_is_repeatable_and_verifies(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_dataset(root)
            license_file, dataset_card = self.make_documents(root)
            audit = root / "audit"
            audit.mkdir()
            (audit / "review-decisions.json").write_text("{}\n")
            first = build_dataset_package(
                "test-data",
                "1",
                "datasets-1",
                source,
                "manifest.ground-truth.json",
                root / "one",
                license_file,
                dataset_card,
                [("prior", audit)],
            )
            second = build_dataset_package(
                "test-data",
                "1",
                "datasets-1",
                source,
                "manifest.ground-truth.json",
                root / "two",
                license_file,
                dataset_card,
                [("prior", audit)],
            )
            self.assertEqual(first["sha256"], second["sha256"])
            result = verify_dataset_package(
                Path(first["path"]), first["sha256"]
            )
            self.assertEqual(result["id"], "test-data/1")
            self.assertEqual(result["sample_count"], 3)
            self.assertEqual(result["included_sample_count"], 2)
            self.assertEqual(result["file_count"], 8)

    def test_missing_included_image_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_dataset(root)
            (source / "images/train/flat.png").unlink()
            license_file, dataset_card = self.make_documents(root)
            with self.assertRaisesRegex(ValueError, "image does not exist"):
                build_dataset_package(
                    "test-data",
                    "1",
                    "datasets-1",
                    source,
                    "manifest.ground-truth.json",
                    root / "dist",
                    license_file,
                    dataset_card,
                    [],
                )

    def test_wrong_archive_checksum_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_dataset(root)
            license_file, dataset_card = self.make_documents(root)
            built = build_dataset_package(
                "test-data",
                "1",
                "datasets-1",
                source,
                "manifest.ground-truth.json",
                root / "dist",
                license_file,
                dataset_card,
                [],
            )
            with self.assertRaisesRegex(ValueError, "package checksum"):
                verify_dataset_package(Path(built["path"]), "0" * 64)


if __name__ == "__main__":
    unittest.main()
