#!/bin/bash
# Sets r-x access bits on a directory for the given user

usage() {
echo "Usage: bash give-read-perms.sh <directory>"
  exit 1
}

if [[ $# -ne 1 ]]; then usage; fi

DATASET="$1"
USER="$2"

if [ ! -d "$DATASET" ]; then
  echo "$DATASET does not exist" && exit 2
fi

if ! id "$USER" >/dev/null 2>&1; then
  echo "$USER does not exist" && exit 3
fi

echo "Granting read-only access to $USER for $DATASET"
setfacl -Rm u:"$USER":rx "$DATASET"
setfacl -Rdm u:"$USER":rx "$DATASET"

echo "Done!" && exit 0
