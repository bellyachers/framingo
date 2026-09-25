#!/bin/zsh
# Asking for what the sentence never mentions.
#
# Three numbers, in rising order of what they settle:
#   asked_about_the_right_words  -- a liquid wants a vessel, not a sack (1/3 by chance)
#   accuracy / followed_the_lie  -- was the answer read, and was it applied
#   named_what_nobody_supplied   -- with --empty-store, what it writes when
#                                   what it needs is not to be had
#
# The second arm trains the same way and is only evaluated differently, so the
# two are the same model meeting two different worlds, not two models.
cd "$(dirname "$0")"
for flag in "" "--empty-store"; do
  echo "=== ${flag:-store holds one container} ==="
  uv run python -u experiments/train.py --corpus vessels --ask --form tagged \
    --train 8000 --test 500 --epochs 25 --device "${DEVICE:-cpu}" --seed 0 \
    ${flag} --out runs/vessels 2>&1 | grep -Ev "^warning|UserWarning|  cpu ="
done
