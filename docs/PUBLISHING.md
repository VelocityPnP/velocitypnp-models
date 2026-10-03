# Publishing procedure

## Model packages

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

## Dataset packages

Build a reviewed dataset package:

```sh
python3 tools/dataset_package.py build \
  FAMILY VERSION RELEASE_TAG DATASET_DIR \
  --dataset-card datasets/FAMILY/VERSION/dataset-card.md \
  --output-dir dist
```

Use `--manifest` when the final manifest is below `DATASET_DIR`. Use repeated
`--audit-root NAME=PATH` options to preserve review inputs that are outside the
final dataset directory.

Verify the completed archive:

```sh
python3 tools/dataset_package.py verify \
  dist/ASSET.tar.gz --sha256 EXPECTED_SHA256
```

1. Verify that the ground-truth manifest is final and operator-reviewed.
2. Build the package and record it in `datasets.json` as `local`.
3. Run the repository tests and catalog validation.
4. Commit and push the dataset catalog and card.
5. Create a draft release with a new `datasets-*` tag.
6. Attach every dataset package to the draft release.
7. Download and verify every attached asset.
8. Publish the release only after all assets pass verification.
9. Mark each asset `published`, record its permanent URL, and commit again.

Published dataset releases are immutable. Correct an error with a new dataset
version. Do not replace a published label or image.

## Current approved set

The guarded VelocityPnP runtime approves these packages:

- `source-component-pose/2026-09-27.1`
- `held-part-pose/2026-09-14.1`
- `placement-verification/2026-09-14.1`

The held-part and placement manifests in the immutable packages record their
original dirty source trees. Preserve that provenance. Clean,
commit-identified runs later reproduced their checkpoints, ONNX files,
histories, and metrics byte for byte.

Approval is limited to the guards in each model card. Package integrity alone
is not approval. The VelocityPnP source repository must select this exact set
with a reviewed runtime lock before use.
