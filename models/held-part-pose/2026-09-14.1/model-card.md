# Held part pose 2026-09-14.1

Status: **approved**

This model compares bare-nozzle and observed bottom-camera images. It
classifies the retained-part state and estimates the oriented component box.
It implements `velocitypnp.held-part-pose.v1`.

## Data

The reviewed dataset has 307 samples: 274 training samples and 33 evaluation
samples. It combines prior images with the new placement-session images. The
evaluation split has one group and no component-on-edge samples.

Dataset content SHA-256:
`dadcb24a3145c3f75f4f2dfc61c0ec78008fa33f7f40dcfca3948cf7ef09ef79`

## Evaluation

- State accuracy: 1.000
- Occupancy precision: 1.000
- Occupancy recall: 1.000
- Mean center error: 0.367 input pixels
- Mean angle error: 1.475 degrees modulo 180 degrees
- Mean oriented IoU: 0.880

## Limitations

The evaluation split is small, contains one group, and has no on-edge held
parts. Its rotation stress set is synthetic. The published training manifest
records a dirty source tree. A clean, commit-identified rerun reproduced the
checkpoint, ONNX file, training history, and metrics byte for byte.

## Approval scope

This model is approved for the current guarded VelocityPnP held-part and
clear-nozzle checks. Existing package, shape, and vacuum checks remain in
force. The approval does not give an on-edge, condition, or pose result sole
authority over machine control.
