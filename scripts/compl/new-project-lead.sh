#!/bin/bash
# A script to grant a project lead/leads full read write access to a project.

# USAGE: bash new-project-lead.sh <user1>,<user2> <project>

usage() { echo "Usage: bash $0 <user1>,<user2>,... <project>"; exit 0; }

if [[ $# -ne 2 ]]; then usage; fi

proj_leads=$1
proj_leads=${proj_leads//,/ }
project=$2
DATA_PATH=/home/data/NDClab/datasets
TOOL_PATH=/home/data/NDClab/tools
ANA_PATH=/home/data/NDClab/analyses
LAB_USERS_TXT="/home/data/NDClab/tools/lab-devOps/scripts/configs/group.txt"

function verify_lead
{
    b_group=$(cat $LAB_USERS_TXT)
    b_group=(${b_group//,/ })
    for i in "${b_group[@]}"
    do
        if [ $i == $1 ]; then
            echo "true" && return
        fi
    done
    echo "false"
}

for proj_lead in ${proj_leads}; do
  unset added
  if [[ ! $(verify_lead $proj_lead) == "true" ]]; then
    echo "User $proj_lead not found in hpc_gbuzzell group" && exit 1
  fi

  if [[ -d `realpath $project` ]]; then #full path provided
    project=`realpath $project`
    echo "granting $proj_lead read write access to $project"
    setfacl -Rm d:u:$proj_lead:rwx,u:$proj_lead:rwx $project
    added=true
  else #search for project name in lab folders
    for dir in $DATA_PATH $TOOL_PATH $ANA_PATH; do
      for repo in $(ls $dir); do
        if [[ $repo == $project ]]; then
          echo "granting $proj_lead read write access to $(basename $dir)/$project"
          setfacl -Rm d:u:$proj_lead:rwx,u:$proj_lead:rwx $dir/$project
          added=true
        fi
      done
    done
  fi
  if [[ $added == "" ]]; then echo "project $project not found, $proj_lead not added" && exit 2; fi
done
