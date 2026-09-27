# Source-component dataset 2026-09-26.1

This dataset combines all retained top-camera feeder component images through
September 26, 2026, with the prior reviewed source-component data.

It contains 595 records. Of these, 567 are included: 501 for training and 66
for evaluation. The included labels contain 336 flat components, 51 on-edge
components, and 180 empty pockets. The other 28 records are rejected.

The package contains the final ground-truth manifest, all reviewed images,
the original and resumed review records, model proposals, deterministic
proposals, and carried-label provenance. The September 26 review accepted 198
parts, marked 122 pockets empty, and rejected 16 images.

The current model seeded unfinished boxes before operator review. Model
confidence did not suppress proposals or create ground truth. The operator
reviewed or corrected every final decision.

The evaluation split is inherited from earlier training work and is not an
independent deployment test for a model trained from this dataset. Capture
and review a new holdout before model approval or activation.
