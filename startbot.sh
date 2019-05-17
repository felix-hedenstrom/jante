#!/bin/bash
# This is only useful if one uses jante in a git repo to allow for fast updates.
while true; do
  python3 -O bot.py -x 
  echo "Pulling..."
  git pull -q
  echo "Finished pulling!"
  sleep 4
done
