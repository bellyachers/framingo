#!/bin/zsh
cd "$(dirname "$0")"
while pgrep -f "corpus scaled" >/dev/null; do sleep 30; done
DEVICE=mps ./run-capacity.sh > runs/capacity.log 2>&1
echo "capacity sweep finished"
