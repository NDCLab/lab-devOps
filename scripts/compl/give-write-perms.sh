#!/bin/bash
# Sets rwx access bits on a directory for the given user

usage() {
echo "Usage: bash give-write-perms.sh <directory> <user>"
  exit 1
}

if [[ $# -ne 2 ]]; then usage; fi

DATASET="$1"
USER="$2"

if [ ! -d "$DATASET" ]; then
  echo "$DATASET does not exist" && exit 2
fi

if ! id "$USER" >/dev/null 2>&1; then
  echo "$USER does not exist" && exit 3
fi

echo "Granting full access to $USER for $DATASET"
setfacl -Rm u:"$USER":rwx "$DATASET"
setfacl -Rdm u:"$USER":rwx "$DATASET"

echo "Done!" && exit 0
