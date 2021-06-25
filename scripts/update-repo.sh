#!/bin/bash
REPOSITORIES=`../..`

IFS=$'\n'

for REPO in `ls "$REPOSITORIES/"`
do
  if [ -d "$REPOSITORIES/$REPO" ]
  then
    if [ -d "$REPOSITORIES/$REPO/.git" ]
    then
      cd "$REPOSITORIES/$REPO"
      git fetch
      git pull
    else
      echo "Skipping"
    fi
  fi
done