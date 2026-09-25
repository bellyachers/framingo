#!/bin/zsh
# The experiment `journal/findings/the-scale-question.md` designed and nobody
# ran. Classes are swept with the model held fixed, so the curve says how much
# of the world a model of this size can carry.
#
# What to read out of it, written before the numbers exist:
#   - a gentle fall with N            -> capacity-bound, nothing qualitative
#   - a cliff at some N               -> something broke; read the outputs
#   - no fall                         -> N is not yet the binding constraint
#   - `unmoved_by_the_lie` rising     -> the model has stopped reading the
#                                        answer and started writing from the
#                                        weights. That is the point where the
#                                        separation fails, and it is the number
#                                        this sweep exists to find.
cd "$(dirname "$0")"
for n in 10 20 40 80 160; do
  echo "=== classes $n ==="
  uv run python -u experiments/train.py --corpus scaled --ask --form tagged \
    --classes $n --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 20 \
    --device "${DEVICE:-cpu}" --seed 0 --out runs/scale 2>&1 \
    | grep -Ev "^warning|UserWarning|  cpu ="
done
