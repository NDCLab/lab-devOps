#!/bin/bash

usage() {
  echo "Usage: bash offboard-user.sh <user>"
  exit 1
}

if [[ $# -ne 1 ]]; then usage; fi

USER="$1"
DIR="/home/data/NDClab"

if ! id "$USER" >/dev/null 2>&1; then
  echo "$USER does not exist" && exit 3
fi

setfacl -Rm u:"$USER":--- "$DIR"
setfacl -Rdm u:"$USER":--- "$DIR"
