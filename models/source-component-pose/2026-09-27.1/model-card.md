# Source component pose 2026-09-27.1

Status: **approved**

This model classifies strip-feeder pockets and estimates the oriented box of
a visible component. It implements `velocitypnp.source-component-pose.v2`.
It does not determine component polarity.

## Data

The reviewed dataset has 588 included samples: 502 training samples and 86
evaluation samples. The training split has 298 flat components, 40 on-edge
components, and 164 empty pockets. The evaluation split has 57 flat
components, four on-edge components, and 25 empty pockets.

Dataset content SHA-256:
`d5ce0faad8bbadabff1c15c0940917887ec40ca6fc82f09139376207c880c9b2`

## Training

The clean CUDA run used source commit `0d6427d` and seed 0. It selected base
epoch 91 and classifier-calibration epoch 24. The classifier used the
evaluation-first selection policy and hard-negative weight 2. A second run
produced identical checkpoints, ONNX files, histories, and evaluation
records.

## Evaluation

- Occupancy precision: 1.000
- Occupancy recall: 0.951
- Class accuracy: 83 of 86
- Mean center error: 0.558 input pixels
- Mean angle error: 1.031 degrees modulo 180 degrees
- Mean oriented IoU: 0.883
- On-edge class accuracy: 3 of 4 evaluation and 16 of 40 training images
- ONNX reference parity: passed with zero class differences
- Tract runtime: three evaluation class errors

A new 21-image feeder holdout passed 21 of 21 flat-versus-empty class checks
in the Tract runtime. Sixteen images used pocket positions excluded from this
model's training data. Five images were repeated position controls. The prior
model failed three of these checks by classifying flat components as on-edge.

Holdout dataset: `source-component-holdout/2026-09-27.1`

Holdout content SHA-256:
`dbe506a7268908261d0607f4fee613274b16b5c7c122a067426a4658db566820`

## Limitations

The training evaluation split guided model selection and is not independent.
It has only four on-edge examples. The model misses 24 of 40 on-edge training
images.

The new holdout contained no on-edge parts, so it does not validate on-edge
recall. Its component boxes were seeded by this model and accepted without
material edits, so it is not an independent localization test.

## Approval scope

This model is approved for the guarded VelocityPnP runtime. A high-confidence
flat-component center can control pickup only inside the configured confidence,
offset, and deterministic-disagreement bounds. An empty result can change
pocket state only when the learned and deterministic results agree.

The approval does not cover broader on-edge decisions or unrestricted learned
localization. Those uses still need an on-edge holdout and an independent
localization check. Publishing or approving this package does not activate it.
