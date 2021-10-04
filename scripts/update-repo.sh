#!/bin/bash
IFS=$'\n'

echo "Checking repos in tools"
for REPO in `ls "/home/data/NDClab/tools/"`
do
  echo "Checking $REPO"
  if [ -e "/home/data/NDClab/tools/$REPO/.git" ]
    then
      cd "/home/data/NDClab/scripts/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
  fi
done

echo "Checking repos in datasets"
for REPO in `ls "/home/data/NDClab/datasets"`
do
  echo "Checking $REPO"
  if [ -e "/home/data/NDClab/datasets/$REPO/.git" ]
    then
      cd "home/data/NDClab/datasets/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
   fi
done

echo "Checking repos in analyses"
for REPO in `ls "/home/data/NDClab/analyses"`
do
  echo "Checking $REPO"
  if [ -e "/home/data/NDClab/analyses/$REPO/.git" ]
    then
      cd "home/data/NDClab/datasets/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
   fi
done

