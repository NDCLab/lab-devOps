#!/bin/bash
# A script to grant a project lead full read write access to a project.

# USAGE: bash new-project-lead.sh <user> <project>

usage() { echo "Usage: bash $0 <user> <project>"; exit 0; }

if [[ $# -ne 2 ]]; then usage; fi

proj_lead=$1
project=$2
DATA_PATH=/home/data/NDClab/datasets
TOOL_PATH=/home/data/NDClab/tools
ANA_PATH=/home/data/NDClab/analyses

function verify_lead
{
    b_group=$(getent group hpc_gbuzzell)
    b_group=(${b_group//,/ })
    b_group[0]=$(echo ${b_group[0]} | cut -d":" -f4)
    for i in "${b_group[@]}"
    do
        if [ $i == $1 ]; then
            echo "true" && return
        fi
    done
    echo "false"
}

if [[ ! $(verify_lead $proj_lead) == "true" ]]; then
  echo "User $proj_lead not found in hpc_gbuzzell group" && exit
fi

for dir in $DATA_PATH $TOOL_PATH $ANA_PATH; do
  for repo in $(ls $dir); do
    if [[ $repo == $project ]]; then
      echo "granting $proj_lead read write access to $(basename $dir)/$project"
      setfacl d:u:$proj_lead:rwx,u:$proj_lead:rwx $dir/$project
      added=true && break 2
    fi
  done
done

if [[ $added == "" ]]; then echo "project $project not found, $proj_lead not added" && exit 1
