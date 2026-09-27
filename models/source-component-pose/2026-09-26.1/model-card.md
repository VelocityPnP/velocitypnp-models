# Source component pose 2026-09-26.1

Status: **candidate**

This model classifies strip-feeder pockets and estimates the oriented box of
a visible component. It implements `velocitypnp.source-component-pose.v2`.
It does not determine component polarity.

## Data

The reviewed dataset has 567 included samples: 501 training samples and 66
evaluation samples. The training split has 293 flat components, 48 on-edge
components, and 160 empty pockets. The evaluation split has 43 flat
components, three on-edge components, and 20 empty pockets.

Dataset content SHA-256:
`e108470370b3aebf0ac986b710c9755ad11cb844d5ae3a0a09ff345029ea8673`

## Training

The clean CUDA run used source commit `0d6427d` and seed 0. It selected base
epoch 144 and classifier-calibration epoch 14. A second run produced identical
checkpoints, ONNX files, training history, and classifier history.

## Evaluation

- Occupancy precision: 1.000
- Occupancy recall: 0.978
- Class accuracy: 65 of 66
- Mean center error: 0.470 input pixels
- Mean angle error: 1.072 degrees modulo 180 degrees
- Mean oriented IoU: 0.887
- On-edge class accuracy: 3 of 3 evaluation and 31 of 48 training images
- ONNX reference parity: passed with zero class differences
- Tract runtime: one evaluation class error, matching the training report

The one evaluation error is a flat component classified as empty. The pose
head still placed its box with 0.184 input-pixel center error and 0.952 IoU.

## Limitations

The evaluation split was also used for v4 and v5 model selection. It is not
an independent holdout. It has only three on-edge examples. The model misses
17 of 48 on-edge training images and one flat evaluation image.

Tract can emit negative infinity for a saturated class log-probability. Source
commit `22abb29` accepts this valid zero-probability value while it continues
to reject NaN, positive infinity, all-negative-infinity class output, and
non-finite pose output.

Keep this model in candidate state until it passes a new independent feeder
holdout and the package is tested through the application runtime. Do not
activate it from these reused evaluation results.
