#!/bin/bash
IFS=$'\n'

for REPO in `ls "/home/data/NDClab/scripts/"`
do
  echo "Checking $REPO"
  if [ -e "/home/data/NDClab/scripts/$REPO/.git" ]
    then
      cd "/home/data/NDClab/scripts/$REPO"
      git fetch
      git pull
      git push
    else
      echo "Skipping"
  fi
done
