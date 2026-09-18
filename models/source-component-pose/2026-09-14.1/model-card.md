# Source component pose 2026-09-14.1

Status: **candidate**

This model classifies strip-feeder pockets and estimates the oriented box of
a visible component. It implements `velocitypnp.source-component-pose.v2`.
It does not determine component polarity.

## Data

The reviewed dataset has 201 samples: 161 training samples and 40 evaluation
samples. It combines prior feeder images with the new feeder sessions. The
evaluation split has no component-on-edge samples.

Dataset content SHA-256:
`5f06a4f1dbc2f1e9d6d28e97024c7501b30d41389c6af1812b90512a7afdff04`

## Evaluation

- Occupancy precision: 1.000
- Occupancy recall: 0.800
- Mean center error: 1.039 input pixels
- Mean angle error: 2.080 degrees modulo 180 degrees
- Mean oriented IoU: 0.768
- ONNX parity: passed with zero class mismatches

## Limitations

The evaluation split is small and has no component-on-edge samples. The data
comes from one machine and a small number of sessions. The training manifest
records a dirty source tree. Keep this model in candidate state until it has
independent evaluation and runtime validation.
