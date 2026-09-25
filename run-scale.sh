#!/bin/zsh
# The experiment `journal/findings/the-scale-question.md` designed and nobody
# ran, with the arm that makes it decide something.
#
# Both arms see the same world at each size. One may fetch what it derives;
# the other may not and has to hold the composite table in its weights. The
# table grows with the number of classes and the model does not.
#
#   the fetching arm holds up and the other falls away
#       -> **not yet** proposition 1. At --train 8000 and 160 classes there
#          are about seventeen examples per (verb, class), so the arm that
#          has to hold the table may be short of data rather than short of
#          parameters. Raise --train at the size where it fell and see
#          whether it recovers. Only if it does not is this about capacity.
#   both fall together
#       -> the limit is elsewhere; read what breaks
#   neither falls
#       -> 160 classes is still a toy. Raise it
#
# And in the fetching arm, watch `unmoved_by_the_lie` rise. That is the model
# ceasing to read what it asked for and answering from the weights instead,
# and it is the point at which the arrangement stops being what it claims.
# Nothing else in the run reports it, because the accuracy would not move.
cd "$(dirname "$0")"
for n in 10 20 40 80 160; do
  for flag in "--ask" ""; do
    echo "=== classes $n ${flag:-no-ask} ==="
    uv run python -u experiments/train.py --corpus scaled --form tagged \
      --classes $n --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 20 \
      --device "${DEVICE:-cpu}" --seed 0 ${flag} --out runs/scale
  done
done
