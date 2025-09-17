#!/bin/bash

DIR="/home/data/NDClab"
GROUPNAME="hpc_gbuzzell"

for dataset in "$DIR/datasets"/*/; do
  dataset=$(basename "$dataset")
  for protected in "sourcedata" "derivatives"; do
    if [ -d "$DIR/datasets/$dataset/$protected" ]; then
      echo "Restricting access to $dataset/$protected"
      setfacl -Rm g:"$GROUPNAME":---,g::--- "$DIR/datasets/$dataset/$protected"
      setfacl -Rdm g:"$GROUPNAME":---,g::--- "$DIR/datasets/$dataset/$protected"
    fi
  done
done
