#!/bin/zsh
# How much longer does the memorising route take as the world grows?
#
# At 160 classes it needs sixty epochs to reach 0.994 where the fetching route
# needs twenty. At 320 classes, twenty epochs leave it at 0.142. The question
# the budget sweep left open is what number replaces sixty here.
#
#   it needs about twice sixty
#       -> the cost of memorising grows with the world about as fast as the
#          world does. The gap is a constant factor, worth having and no more.
#   it needs much more than twice, or does not get there at all
#       -> the cost grows faster than the world, and the fetching route's
#          advantage compounds. That is the strong form of the claim and the
#          one worth taking to a larger world.
#
# 160 classes took sixty; 320 is twice the world, so 120 is the linear
# prediction and 400 is the ceiling this asks about.
cd "$(dirname "$0")/../.."   # the repository root
for e in 60 120 250 400; do
  echo "=== no-ask classes 320 epochs $e ==="
  uv run python -u experiments/train.py --corpus scaled --form tagged \
    --classes 320 --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs $e \
    --d 64 --layers 2 --device "${DEVICE:-mps}" --seed 0 --out runs/e320-$e
done
echo "=== ask classes 320 epochs 60 (for reference) ==="
uv run python -u experiments/train.py --corpus scaled --form tagged \
  --classes 320 --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 60 \
  --d 64 --layers 2 --device "${DEVICE:-mps}" --seed 0 --ask --out runs/e320-ask60
