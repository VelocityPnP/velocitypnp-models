# Source-component dataset 2026-09-20.1

This dataset combines the prior reviewed feeder data with the reviewed
September 20 holdout.

It contains 259 records. Of these, 247 are included: 181 for training and 66
for evaluation. Both splits contain empty pockets, flat components, and
on-edge components.

The package contains the final ground-truth manifest and reviewed images. Its
audit directory contains the September 20 review decisions. The earlier 213
labels are preserved in source-component dataset `2026-09-14.1` and identified
by source manifest checksums.

The September 20 holdout became training data during this merge. It is not an
independent deployment test.
