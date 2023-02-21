#!/bin/bash
# A script to remove id from all datasets & analysis, or if p is specified certain datasets & analyses

# USAGE: remove <id> [ -p <project1,project2,... ]
usage() { echo "Usage: bash remove.sh <id> [ -p <project1,project2,... ]"; exit 0; }

if [[ $# -eq 0 ]]; then usage; fi

id=$1

while getopts "p:" opt; do
  case "${opt}" in
    p)
      proj=${OPTARG}
      proj=${proj//,/ }
      ;;
    *)
      usage
      ;;
  esac
done

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"
tpath="/home/data/NDClab/tools"

if [[ $proj == "" ]]; then
  # remove from all repo ACL's
  for dir in $dpath $apath $tpath; do
    for repo in `ls $dir`; do
      echo "removing $id from $repo"
      setfacl -Rx u:$id,d:u:$id "${dir}/${repo}"
    done
  done
else
  for dir in $dpath $apath $tpath; do
    for repo in `ls $dir`; do
      if [[ "$proj" =~ .*"$repo".* ]]; then
        echo "removing $id from $repo"
        setfacl -Rx u:$id,d:u:$id "${dir}/${repo}"
      fi
    done
  done
fi
