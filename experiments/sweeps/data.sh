#!/bin/zsh
# Is the fetching route's advantage only there because the data is thin?
#
# At 320 classes the core has ~966 rules and training draws 8,000 examples —
# about eight per rule. The memorising arm needed 120 epochs to get there where
# the fetching arm needed 60, and that was read as a cost of memorising. It may
# instead be a cost of seeing each rule eight times.
#
# Epochs and examples are different axes and only the first was swept. This
# sweeps the second, holding epochs at 20 — the budget where the two arms were
# furthest apart.
#
#   the no-ask arm recovers with more data
#       -> the advantage was in the sample, not in the route. Say so: the
#          fetching route is worth having when examples are scarce, which is a
#          narrower claim again and the third narrowing tonight.
#   it does not recover
#       -> the cost of memorising is in the optimisation and not in the sample,
#          and the 2-3x budget factor stands as measured.
cd "$(dirname "$0")/../.."   # the repository root
for n in 8000 32000 128000; do
  for flag in "" "--ask"; do
    echo "=== train $n ${flag:-no-ask} ==="
    uv run python -u experiments/train.py --corpus scaled --form tagged \
      --classes 320 --verbs 4 --marked 1.0 --train $n --test 500 --epochs 20 \
      --d 64 --layers 2 --device "${DEVICE:-mps}" --seed 0 ${flag} \
      --out runs/data-n$n
  done
done
