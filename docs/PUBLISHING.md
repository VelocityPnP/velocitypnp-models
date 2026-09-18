# Publishing procedure

Build a package:

```sh
python3 tools/model_package.py build \
  FAMILY VERSION RELEASE_TAG TRAINING_OUTPUT \
  --model-card models/FAMILY/VERSION/model-card.md \
  --output-dir dist
```

Verify the completed archive against the catalog checksum:

```sh
python3 tools/model_package.py verify \
  dist/ASSET.tar.gz --sha256 EXPECTED_SHA256
```

1. Build each package from a completed training-output directory.
2. Verify the package and record its archive checksum in `catalog.json`.
3. Add or update its model card.
4. Run the repository tests and catalog validation.
5. Commit the catalog and model cards.
6. Create a draft GitHub release for the catalog release tag.
7. Attach every package to the draft release.
8. Download the attached assets and verify their recorded checksums.
9. Publish the draft only after all assets pass verification.
10. Set `availability` to `published`, add each download URL, and commit the
    catalog update.

Published releases are immutable. If a package or report is wrong, publish a
new version. Do not delete, replace, or rename a published asset.

A package stays a candidate until it passes independent evaluation and the
VelocityPnP runtime test. Publishing is not approval, selection, or activation.

## Current candidate release

`models-2026-09-14.1` contains three candidate packages from the combined
September 2026 datasets. All three original manifests record a dirty source
tree. Preserve that provenance. Do not mark these models as approved only
because their packages pass integrity checks.
