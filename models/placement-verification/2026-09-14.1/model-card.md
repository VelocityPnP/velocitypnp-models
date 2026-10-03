# Placement verification 2026-09-14.1

Status: **approved**

This model classifies a placement target and estimates the oriented component
box in a normalized top-camera crop. It implements
`velocitypnp.placement-verification.v1`.

## Data

The reviewed dataset has 122 samples: 101 training samples and 21 evaluation
samples. It combines prior images with the new placement-session images. The
evaluation split has five groups and no component-on-edge samples.

Dataset content SHA-256:
`cdeac286ff2614166a3a8927346e3932deb1bd12c8c42b1b5dc8a63b5b08a808`

## Evaluation

- Classification accuracy: 0.810
- Occupancy precision: 0.733
- Occupancy recall: 1.000
- Mean center error: 0.028 mm
- Mean angle error: 3.375 degrees modulo 180 degrees
- Mean oriented IoU: 0.885
- ONNX parity: passed with zero class mismatches

## Limitations

The evaluation split is small and has no component-on-edge samples. The data
comes from one machine and one PCB design. Four empty evaluation sites were
classified as occupied. The published training manifest records a dirty source
tree. A clean, commit-identified rerun reproduced the checkpoint, ONNX file,
training history, and metrics byte for byte.

## Approval scope

This model is approved only with the current deterministic-agreement gate. It
must never be the sole evidence that a placed part exists. The approval does
not remove the existing image, occupancy, pose, or confidence checks.
