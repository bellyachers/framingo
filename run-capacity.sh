#!/bin/zsh
# Where the two arms come apart.
#
# The class sweep held the model at 660k parameters and raised the world to
# 160 classes and 480 rules, and neither arm fell. So the world is not yet the
# binding constraint and growing it further is the expensive way to find out
# where it becomes one. Shrinking the model is the cheap way, and it asks the
# same question from the other side: the arm that fetches holds almost nothing
# — write a variable, ask, apply one rule — while the arm that does not has to
# carry (verb, class) -> tail for every pair in the world.
#
# Pre-registered, because this is the measurement the whole separation is for:
#
#   the no-ask arm falls first, and there is a size where one works and the
#   other does not
#       -> READ `run-epochs.sh` BEFORE BELIEVING THIS. It happened — the arms
#          part between 100k and 166k parameters at twenty epochs — and the
#          epoch control then showed the gap was optimisation, not capacity:
#          the same no-ask arm reaches 0.994 at sixty epochs. What this sweep
#          measures is how fast each route is learned under one budget, which
#          is not charter proposition 1.
#   both fall at the same size
#       -> what limits this model is not the table it has to hold, and
#          proposition 1 does not follow from anything measured here.
#   neither falls at 50k parameters
#       -> the task is too easy at any size to separate them. Say so.
#
# The world is held at 160 classes, where the tables are largest.
cd "$(dirname "$0")"
for size in "128 3" "64 2" "48 2" "32 1" "16 1"; do
  set -- ${=size}
  for flag in "--ask" ""; do
    echo "=== d=$1 layers=$2 ${flag:-no-ask} ==="
    uv run python -u experiments/train.py --corpus scaled --form tagged \
      --classes 160 --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 20 \
      --d $1 --layers $2 --device "${DEVICE:-mps}" --seed 0 ${flag} \
      --out runs/capacity-d$1l$2
  done
done
