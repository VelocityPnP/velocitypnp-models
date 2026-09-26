# Dataset package format

Each package is a deterministic `tar.gz` archive with one top-level directory.
The directory name is `<family>-<version>`.

Required files are:

- `LICENSE`: The package license.
- `dataset-card.md`: Scope, counts, provenance, and limitations.
- `dataset-metadata.json`: Package identity and file checksums.
- `data/`: The final manifest, reviewed images, and local review records.

An optional `audit/` directory contains earlier review inputs used to produce
the final dataset.

The package builder excludes directories named `training`. Model checkpoints,
augmented training images, and evaluation outputs belong in model packages.

The content digest uses the final manifest and exact bytes for every included
training or evaluation image. This is the same digest stored in model
manifests. The package checksum covers excluded records, review decisions,
cards, audit data, and all other package files.

Changing any packaged label, image, or review record requires a new version.
Never replace an asset for an existing version.
