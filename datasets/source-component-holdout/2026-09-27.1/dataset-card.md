# Source-component holdout 2026-09-27.1

This dataset records the September 27 feeder 7 and feeder 8 capture used to
check source-component pose model v6. The capture used safe-Z camera motion
and did not pick components.

It contains 37 records. Twenty-one reviewed records are included in the
evaluation split: 11 flat components and 10 empty pockets. Sixteen records
are excluded because their feeder pocket positions appeared in v6 training.
Of the included records, 16 use new pocket positions and five are repeated
position controls.

The package preserves both operator downloads, the explicit merged review,
the filtered gate review, the finalized labels, and two superseded
finalization attempts. The superseded attempts record one corrected pocket
label and one unintended reject introduced while downloading that correction.

The Tract runtime classified all 21 included records correctly with v6. The
prior v5 model made three flat-to-on-edge errors on the same records.

No on-edge part is present. The component boxes were seeded by v6 and accepted
without material edits. This dataset validates flat-versus-empty
classification, but it does not independently validate on-edge recall or
localization accuracy.
