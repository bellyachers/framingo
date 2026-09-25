#!/bin/zsh
cd "$(dirname "$0")"
while pgrep -f "run-capacity.sh" >/dev/null || pgrep -f "run-epochs.sh" >/dev/null; do sleep 30; done
DEVICE=mps ./run-depth.sh > runs/depth.log 2>&1
echo "depth sweep finished"
