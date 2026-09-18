# Held part pose 2026-09-14.1

Status: **candidate**

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
parts. Its rotation stress set is synthetic. No held-part ONNX parity verifier
exists yet. The training manifest records a dirty source tree. Keep this model
in candidate state until it has independent evaluation and runtime validation.
