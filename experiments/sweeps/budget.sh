#!/bin/zsh
# What externalising knowledge buys, stated as the thing that was actually
# measured rather than the thing that was hoped for.
#
# The capacity sweep's parting turned out to be optimisation: at 157k
# parameters the memorising arm reaches 0.994 given sixty epochs instead of
# twenty. So the claim that survives is about how fast each route is learned
# under one budget — and that claim, unlike the parameter one, makes a
# prediction about size.
#
#   The fetching arm's work does not grow with the world: write a variable,
#   ask, apply one rule. The memorising arm's does: (verb, class) -> tail has
#   an entry per pair. So at a fixed budget, the fetching arm should hold flat
#   as classes are added and the memorising arm should fall away.
#
# The earlier class sweep failed to show this because it ran at d=128, where
# both routes are learned inside twenty epochs at every size tried. This one
# runs at d=64, where twenty epochs is the tight budget.
#
#   the no-ask arm falls with N and the ask arm holds
#       -> the gap widens with the world, which is the shape the architecture
#          predicts, and it is a claim about learning and not about parameters
#   both hold, or both fall together
#       -> the budget is not tight in the way this assumes; say so and stop
#          reporting the twenty-epoch parting as meaning anything
cd "$(dirname "$0")/../.."   # the repository root
for n in 20 40 80 160 320; do
  for flag in "--ask" ""; do
    echo "=== classes $n ${flag:-no-ask} ==="
    uv run python -u experiments/train.py --corpus scaled --form tagged \
      --classes $n --verbs 4 --marked 1.0 --train 8000 --test 500 --epochs 20 \
      --d 64 --layers 2 --device "${DEVICE:-mps}" --seed 0 ${flag} \
      --out runs/budget-c$n
  done
done
