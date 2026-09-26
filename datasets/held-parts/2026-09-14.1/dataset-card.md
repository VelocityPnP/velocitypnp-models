# Held-part dataset 2026-09-14.1

This is the reviewed bottom-camera dataset used by held-part model
`2026-09-14.1`.

It contains 308 records. Of these, 307 are included: 274 for training and 33
for evaluation. The labels cover bare nozzles, flat components, and on-edge
components. The evaluation split has no on-edge component.

The package contains paired bare and observed images, the final ground-truth
manifest, review decisions, carried labels, and review provenance. It excludes
model training outputs.

The evaluation split comes from one machine and one feeder registration. Use
independent sessions before model approval.
