#!/bin/bash
# Adds everyone to new repo (except sourcedata and derivatives)

# USAGE: new-dataset.sh <new-repo>
usage() { echo "Usage: bash new-dataset.sh <new-repo> ]"; exit 0; }

if [[ $# -ne 1 ]]; then usage; fi

repo=$1

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"
tpath="/home/data/NDClab/tools"

b_group=$(getent group hpc_gbuzzell)
b_group=(${b_group//,/ })
# remove leading "hpc_gbuzzell:*:284:"
b_group[0]=$(echo ${b_group[0]} | cut -d":" -f4)

for DIR in $dpath $apath $tpath; do
  if [[ "$DIR" == "$repo" ]]; then
    for user in ${b_group[@]}; do
      setfacl -Rm u:$user:r-x,d:u:$user:r-x "$DIR"/"$repo"
      for priv in "sourcedata" "derivatives"; do
        if [[ -d $DIR/$repo/$priv ]]; then
          setfacl -Rm u:$user:---,d:u:$user:--- "$DIR"/"$repo"
        fi
      done
    done
  fi
done
