#!/bin/bash
# A script to remove id from all datasets & analysis

# USAGE: remove <id>
usage() { echo "Usage: bash remove.sh <id>"; exit 0; }

if [[ $# -ne 1 ]]; then usage; fi

id=$1

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"
tpath="/home/data/NDClab/tools"

for dir in $dpath $apath $tpath; do
  for repo in `ls $dir`; do
    echo "removing $id from $repo"
    setfacl -Rx u:$id,d:u:$id "${dir}/${repo}"
  done
done
