#!/bin/zsh
# Width or depth?
#
# The capacity sweep moved both at once — 128x3, 64x2, 48x2, 32x1, 16x1 — so
# the size at which the memorising arm collapses (between 710k at three layers
# and 157k at two) is also the size at which it loses a layer. Either could be
# what it needs.
#
# Four runs separate them, holding the world at 160 classes:
#   d=128 layers=2  -- wide and shallow
#   d=64  layers=3  -- narrow and deep
# If the no-ask arm survives the wide shallow one and not the narrow deep one,
# what it needs is width, which is where a lookup table would live. If it is
# the other way round the collapse was about depth and has little to do with
# holding a table at all.
cd "$(dirname "$0")/../.."   # the repository root
for size in "128 2" "64 3"; do
  set -- ${=size}
  for flag in "--ask" ""; do
    echo "=== d=$1 layers=$2 ${flag:-no-ask} ==="
    uv run python -u experiments/train.py --corpus scaled --form tagged \
      --classes 160 --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 20 \
      --d $1 --layers $2 --device "${DEVICE:-mps}" --seed 0 ${flag} \
      --out runs/depth-d$1l$2
  done
done
