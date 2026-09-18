# Model package format

Each package is a deterministic `tar.gz` archive with one top-level directory.
The directory name is `<family>-<version>`.

Required files are:

- `best.onnx`: Runtime weights.
- `best.pt`: Training checkpoint. Load it only after checksum verification.
- `LICENSE`: The package license.
- `model-card.md`: Intended use, evaluation results, and limitations.
- `model-manifest.json`: The original training manifest.
- `package-metadata.json`: Package identity and a checksum for every file.

Other JSON reports from the training output are included. These can contain
training history, evaluation records, stress-test records, and ONNX parity
results.

The package identity has four independent parts:

1. The family and release version identify the training run.
2. The contract version identifies runtime compatibility.
3. The dataset content digest identifies the reviewed training data.
4. SHA-256 digests identify the package, manifest, checkpoint, and ONNX file.

Changing any packaged file requires a new version and a new archive. Never
replace an asset for an existing version.
