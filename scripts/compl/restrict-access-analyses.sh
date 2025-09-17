#!/bin/bash


DIR="/home/data/NDClab/analyses"
GROUPNAME="hpc_gbuzzell"

for dataset in "$DIR"/*/; do
  dataset=$(basename "$dataset")
  for protected in "sourcedata" "derivatives"; do
    echo "$DIR/$dataset/$protected"
    if [ -d "$DIR/$dataset/$protected" ]; then
      echo "Restricting access to $DIR/$dataset/$protected"
      setfacl -Rm g:"$GROUPNAME":---,g::--- "$DIR/$dataset/$protected"
      setfacl -Rdm g:"$GROUPNAME":---,g::--- "$DIR/$dataset/$protected"
    fi
  done
done


