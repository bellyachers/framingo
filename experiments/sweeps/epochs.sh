#!/bin/zsh
# Capacity or optimisation?
#
# At d=64 the arm that fetches scores 1.000 and the arm that must hold the
# (verb, class) table scores 0.368, both after twenty epochs. That reads as
# the table not fitting — but a bigger table also converges more slowly, and
# 0.368 may be "not in yet" rather than "will not go in".
#
#   it recovers with more epochs -> optimisation. The claim weakens to "under
#       one budget the fetching route is learned faster", which is true but is
#       not proposition 1.
#   it does not recover          -> capacity, and proposition 1 gets its first
#       number: 160 classes and 486 rules need more than 190k parameters to
#       hold, and 190k to fetch.
cd "$(dirname "$0")/../.."   # the repository root
for e in 20 60 150; do
  echo "=== no-ask d=64 epochs $e ==="
  uv run python -u experiments/train.py --corpus scaled --form tagged \
    --classes 160 --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs $e \
    --d 64 --layers 2 --device "${DEVICE:-mps}" --seed 0 --out runs/epochs-e$e
done
