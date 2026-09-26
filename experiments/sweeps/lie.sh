#!/bin/zsh
# Does a trained derivation read what it asked for?
#
# The tail is a function of the input in this world, so the mid-derivation
# answer is never necessary. That makes the lying control the only thing that
# can say whether it is *used*. Epochs are swept because the whole question is
# what happens as the shortcut becomes available: a model that has not yet
# memorised (verb, class) -> tail has to read, one that has does not.
#
# CPU on purpose: an MPS sweep is already running and is worth more than the
# speed of this one.
cd "$(dirname "$0")/../.."   # the repository root
for e in 3 8 20 50; do
  echo "=== epochs $e ==="
  uv run python experiments/train.py --corpus scaled --ask --form tagged \
    --classes 10 --verbs 4 --marked 1.0 --train 8000 --epochs $e \
    --device cpu --seed 0 --out runs/lie-e$e 2>&1 | grep -Ev "^warning|UserWarning|  cpu ="
done
