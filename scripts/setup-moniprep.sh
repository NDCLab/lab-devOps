#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup-data.sh -[f/fd/fn/fdn/dn/n] <project-path>" 1>&2; exit 1; }

project=$1
datam_path="/data-monitoring"
code_path="/code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"

echo "Setting up hallMonitor helper files"
cp "${labpath}/template/rename-cols.py" "${project}/${datam_path}"
cp "${labpath}/template/update-tracker.py" "${project}/${datam_path}"
cp "${labpath}/template/README.md" "${project}/${datam_path}"

echo "Setting up hallMonitor.sh"
cp "${labpath}/template/hallMonitor.sh" "${project}/${datam_path}"
# which task existence needs to be checked
:'
while getopts ":" opt; do
    case ${opt} in
        f)
            ;;
        fd)
             ;;
        fd)
    esac 
done
'
cp "${labpath}/template/hallMonitor.sub" "${project}/${datam_path}"

echo "Setting up preprocess.sub"
cp "${labpath}/template/preprocess.sub" "${project}/${datam_path}"