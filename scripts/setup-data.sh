#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup-data.sh <project-path>" 1>&2; exit 1; }

project=$1
datam_path="/data-monitoring"
code_path="/code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/"

echo "Setting up hallMonitor helper files"
cp "${labpath}/monitor-template/rename-cols.py" "${project}/${datam_path}"
cp "${labpath}/monitor-template/update-tracker.py" "${project}/${datam_path}"
cp "${labpath}/monitor-template/README.md" "${project}/${datam_path}"
echo "Setting up hallMonitor.sh"
cp "${labpath}/monitor-template/hallMonitor.sh" "${project}/${datam_path}"
echo "Setting up hallMonitor.sub"
cp "${labpath}/monitor-template/hallMonitor.sub" "${project}/${datam_path}"

echo "Setting up preprocess.sub"
cp "${labpath}/monitor-template/preprocess.sub" "${project}/${datam_path}"