#!/bin/bash
IFS=$'\n'
TOOL_PATH="/home/data/NDClab/tools"
DATA_PATH="/home/data/NDClab/datasets"
ANA_PATH="/home/data/NDClab/analyses"

echo "Checking repos in tools"
for REPO in `ls $TOOL_PATH`
do
  echo "Checking $REPO"
  if [ -e "$TOOL_PATH/$REPO/.git" ]
    then
      cd "$TOOL_PATH/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
  fi
done

echo "Checking repos in datasets"
for REPO in `ls $DATA_PATH`
do
  echo "Checking $REPO"
  if [ -e "$DATA_PATH/$REPO/.git" ]
    then
      cd "$DATA_PATH/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
   fi
done

echo "Checking repos in analyses"
for REPO in `ls $ANA_PATH`
do
  echo "Checking $REPO"
  if [ -e "$ANA_PATH/$REPO/.git" ]
    then
      cd "$ANA_PATH/$REPO"
      git fetch
      git pull
    else
      echo "Not a git repo. Skipping."
   fi
done

