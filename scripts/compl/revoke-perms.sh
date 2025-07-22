#!/bin/bash

# Revokes user-specific ACL entries for a directory, returning them to default lab group
# permissions (r-x everywhere except sourcedata/ and derivatives/).

usage() {
  echo "Usage: bash revoke-perms.sh <directory>"
  exit 1
}

if [[ $# -ne 1 ]]; then usage; fi

DIR="$1"
USER="$2"

if [ ! -d "$DIR" ]; then
  echo "$DIR does not exist" && exit 2
fi

if ! id "$USER" >/dev/null 2>&1; then
  echo "$USER does not exist" && exit 3
fi

echo "Resetting permissions for $USER"
setfacl -Rx u:"$USER" "$DIR"
setfacl -Rdx u:"$USER" "$DIR"

echo "Done!" && exit 0
