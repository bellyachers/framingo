#!/bin/zsh
cd "$(dirname "$0")"
while pgrep -f "run-capacity.sh" >/dev/null; do sleep 30; done
DEVICE=mps ./run-epochs.sh > runs/epochs.log 2>&1
echo "epoch sweep finished"
