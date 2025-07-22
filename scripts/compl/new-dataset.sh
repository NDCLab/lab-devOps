#!/bin/bash
# Sets --- access bits by default for the hpc_gbuzzell group

# USAGE: new-dataset.sh <new-repo>
usage() {
  echo "Usage: bash new-dataset.sh <new-repo>"
  exit 1
}

if [[ $# -ne 1 ]]; then usage; fi

DATASET="$1"
GROUPNAME="hpc_gbuzzell"

if [ ! -d "$DATASET" ]; then
  echo "$DATASET does not exist" && exit 1
fi

# Set null perms for sensitive directories
for dir in "sourcedata" "derivatives"; do
  if [ -d "$DATASET/$dir" ]; then
    echo "Restricting access to $DATASET/$dir"
    setfacl -Rm g:"$GROUPNAME":---,g::--- "$DATASET/$dir"
    setfacl -Rdm g:"$GROUPNAME":---,g::--- "$DATASET/$dir"
  fi
done
