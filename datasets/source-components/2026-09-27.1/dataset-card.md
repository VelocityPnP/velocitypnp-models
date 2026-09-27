# Source-component dataset 2026-09-27.1

This dataset combines the reviewed source-component data through September
27, 2026. It includes the corrected September 26 labels and the reviewed
holdout that exposed the prior model's on-edge false positives.

It contains 616 records. Of these, 588 are included: 502 for training and 86
for evaluation. The included labels contain 355 flat components, 44 on-edge
components, and 189 empty pockets. The other 28 records are rejected.

A focused audit reviewed all 51 labels that were previously marked on-edge.
The audit changed eight training labels from on-edge to flat. The later
21-image feeder holdout entered this training dataset after it exposed the
prior model defect. It is not an independent test for a model trained from
this dataset.

The package contains the merged ground-truth manifest and all images. Its
audit data also preserves the source manifests, review decisions, and focused
class-audit record used to make the merged labels.

The evaluation split is inherited from earlier model selection. Capture and
review a new holdout before model approval or activation.
