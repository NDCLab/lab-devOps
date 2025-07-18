#!/bin/bash
# Adds everyone to new repo (except sourcedata and derivatives)

# USAGE: new-dataset.sh <new-repo>
usage() {
  echo "Usage: bash new-dataset.sh <new-repo> ]"
  exit 0
}

if [[ $# -ne 1 ]]; then usage; fi

repo=$1

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"
tpath="/home/data/NDClab/tools"
LAB_USERS_TXT="/home/data/NDClab/tools/lab-devOps/scripts/configs/group.txt"

GROUP_NAME="hpc_gbuzzell"

b_group=$(cat $LAB_USERS_TXT)
b_group=(${b_group//,/ })

if [[ -d $repo ]]; then
  for user in ${b_group[@]}; do
    setfacl -Rm u:$user:r-x,d:u:$user:r-x "$repo"
    setfacl -Rm d:group:"$GROUP_NAME":rwx,group:"$GROUP_NAME":rwx "$repo"
    for priv in "sourcedata" "derivatives"; do
      if [[ -d $repo/$priv ]]; then
        setfacl -Rm u:$user:---,d:u:$user:--- $repo/$priv
      fi
    done
  done

else
  for DIR in $dpath $apath $tpath; do
    if [[ "$DIR" == "$repo" ]]; then
      for user in ${b_group[@]}; do
        setfacl -Rm u:$user:r-x,d:u:$user:r-x $DIR/$repo
        setfacl -Rm d:group:"$GROUP_NAME":rwx,group:"$GROUP_NAME":rwx "$DIR/$repo"
        for priv in "sourcedata" "derivatives"; do
          if [[ -d $DIR/$repo/$priv ]]; then
            setfacl -Rm u:$user:--- $DIR/$repo/$priv
          fi
        done
      done
    fi
  done
fi
