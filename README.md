# VelocityPnP models

This repository records immutable learned-model and reviewed-dataset packages
for VelocityPnP. It contains catalogs, cards, package tools, checksums, and
release procedures. Binary packages are GitHub release assets.

A catalog entry does not activate a model. The VelocityPnP source repository
selects an exact package with a reviewed lockfile. The daemon then validates
the package manifest and ONNX checksum before it loads the model.

## Model states

- `candidate`: Packaged, but not approved for machine control.
- `validated`: Independent evaluation and runtime checks passed.
- `approved`: Eligible for explicit selection by a source-repository lockfile.
- `retired`: Retained for rollback and audit, but not for new selection.

State changes update the catalog. They never replace a package or reuse a
version identifier.

## Local checks

```sh
python3 -m unittest discover -s tests
python3 tools/verify_repository.py
```

The model catalog is `catalog.json`. The reviewed-dataset catalog is
`datasets.json`. A model entry names the exact dataset entry whose content
digest is in the model manifest.

See `docs/PACKAGE_FORMAT.md`, `docs/DATASET_FORMAT.md`, and
`docs/PUBLISHING.md` before a release.
