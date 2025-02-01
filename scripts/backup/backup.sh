#!/bin/bash -l
# login shell necessary to use modules in cron jobs

SINGULARITY_VERSION="3.8.2"
PYTHON_CONTAINER="/home/data/NDClab/tools/containers/python-3.9/python-3.9.simg"
BACKUP_PYSCRIPT="/home/data/NDClab/tools/lab-devOps/scripts/backup/backup.py"

module load "singularity-$SINGULARITY_VERSION"
singularity exec -e "$PYTHON_CONTAINER" python3 -u "$BACKUP_PYSCRIPT"
