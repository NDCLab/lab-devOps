#!/bin/bash

SINGULARITY_VERSION="3.8.2"
PYTHON_CONTAINER="/home/data/NDClab/tools/containers/python-3.9/python-3.9.simg"
BACKUP_PYSCRIPT="/home/data/NDClab/tools/lab-devOps/scripts/backup/backup.py"
OUT_FILE=/home/data/NDClab/other/logs/backups/$(date +%m_%d_%Y::%H:%M:%S).log

module load "singularity-$SINGULARITY_VERSION"
singularity exec -e "$PYTHON_CONTAINER" python3 -u "$BACKUP_PYSCRIPT" >"$OUT_FILE"
