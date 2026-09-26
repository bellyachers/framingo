#!/bin/zsh
# The control the lying result needs and did not have.
#
# The claim was: in this world the tail is a function of the input, so the
# mid-derivation lookup is never necessary — and the model performs it anyway.
# The first half was shown structurally, and on `basics`, where the outcome
# word is written out. On `scaled` at --marked 1.0 **every outcome word is
# anonymised**, so the model writes a variable and cannot name the word it
# derived. Whether the tail is still reachable from the input alone is then an
# open question, not a settled one: the long route (target's class from the
# dictionary, then the rule) exists on paper, but paper is not evidence.
#
# If this arm solves it, the lying result means what it was read to mean: two
# routes, and the model took the short one. If it does not, the lookup was
# necessary after all and the headline is wrong.
cd "$(dirname "$0")/../.."   # the repository root
uv run python -u experiments/train.py --corpus scaled --form tagged \
  --classes 10 --verbs 4 --marked 1.0 --train 8000 --test 1000 --epochs 20 \
  --device "${DEVICE:-cpu}" --seed 0 --out runs/noask-scaled > runs/noask-scaled.log 2>&1
tail -4 runs/noask-scaled.log
