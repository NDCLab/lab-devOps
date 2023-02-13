#!/bin/bash
# A script to grant read access to all lab project repos to a new team member.

# USAGE: bash onboard-new.sh <user> 

usage() { echo "Usage: bash $0 <user1>"; exit 0; }

if [[ $# -eq 0 ]]; then usage; fi

ID=$1
DATA_PATH=/home/data/NDClab/datasets
TOOL_PATH=/home/data/NDClab/tools
ANA_PATH=/home/data/NDClab/analyses

for dir in $DATA_PATH $TOOL_PATH $ANA_PATH
  do
  for repo in $(ls $dir)
    do
    setfacl -Rm d:u:$ID:r-x,u:$ID:r-x $dir/$repo
    if [[ $dir == "$DATA_PATH" ]]; then
      setfacl -Rm d:u:$ID:---,u:$ID:--- $dir/$repo/sourcedata
      setfacl -Rm d:u:$ID:---,u:$ID:--- $dir/$repo/derivatives
      # don't grant access to sourcedata and derivatives
    fi
  done
done
