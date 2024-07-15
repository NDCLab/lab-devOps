#!/bin/bash

PYIMG="/home/data/NDClab/tools/containers/python-3.8/python-3.8.simg"
dset="thrive-dataset"
current_submission="jul-2024-submission"
##dset=${1}
##current_submission=${2}

singularity exec -e $PYIMG bash -c "python3 new_ndar_submission.py $dset $current_submission"

# Directory to search for folders
search_directory="/home/data/NDClab/datasets/$dset/data-monitoring/ndar/$current_submission/eeg"

# Change to the search directory
cd "$search_directory"

# Find all directories and zip them
find . -mindepth 1 -maxdepth 1 -type d -exec sh -c 'zip -r "${1%/}.zip" "$1"' _ {} \;

echo "Zipping of folders complete."
