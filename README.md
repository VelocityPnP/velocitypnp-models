# VelocityPnP models

This repository is the public model and reviewed-dataset catalog for
[VelocityPnP](https://github.com/VelocityPnP/VelocityPnP). It contains model
cards, dataset cards, package tools, checksums, and release procedures.
Published binary packages are GitHub release assets.

A catalog entry does not activate a model. The VelocityPnP source repository
selects exact packages with a reviewed lockfile. The daemon checks each package
manifest, file inventory, contract, and ONNX checksum before use.

## Catalogs

- [`catalog.json`](catalog.json) lists learned-model packages and states.
- [`datasets.json`](datasets.json) lists reviewed-dataset packages.
- [`docs/PACKAGE_FORMAT.md`](docs/PACKAGE_FORMAT.md) defines model packages.
- [`docs/DATASET_FORMAT.md`](docs/DATASET_FORMAT.md) defines dataset packages.
- [`docs/PUBLISHING.md`](docs/PUBLISHING.md) defines the release process.

Model states are:

- `candidate`: packaged, but not approved for machine control;
- `validated`: independent evaluation and runtime checks passed;
- `approved`: eligible for selection by a source-repository lockfile; and
- `retired`: retained for audit, but not for new selection.

State changes update the catalog. They do not replace a package or reuse a
version identifier. Model cards define the limits of each approval.

## Local checks

```sh
python3 -m unittest discover -s tests
python3 tools/verify_repository.py
```

Run both commands before a catalog, card, schema, or packaging-tool change.
See [Contributing](CONTRIBUTING.md) before you submit a change.

## Maintainer

[Tim Smith on GitHub](https://github.com/timbot) ·
[Tim Smith on X](https://x.com/timbot)

## License

Repository content and packaged artifacts use the
[Apache License 2.0](LICENSE), unless a package states otherwise.
