#!/bin/zsh
# Wait for the MPS sweep in the other tree to finish, then take the GPU.
# Output goes straight to a file: piping a long job through grep buffers it,
# and a job whose output does not move looks hung.
cd "$(dirname "$0")"
while pgrep -f "corpus basics --form tagged --seed" >/dev/null; do sleep 30; done
DEVICE=mps ./run-scale.sh > runs/scale.log 2>&1
echo "scale sweep finished"
