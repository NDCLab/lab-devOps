#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup-data.sh <project-path> [filetype1,filetype2,filetype3] [task1,task2,task3] " 1>&2; exit 1; }

# HallMonitor construction args
project=$1
filetypes=$2
# Optional tasks arg 
tasks=${3:-0}

datam_path="/data-monitoring"
code_path="/code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"

echo "Setting up hallMonitor helper files"
# delete if previously written
cp "${labpath}/template/rename-cols.py" "${project}/${datam_path}"
cp "${labpath}/template/update-tracker.py" "${project}/${datam_path}"

echo "Setting up hallMonitor.sh"
# delete if previously written
# set up hallMonitor sh file with preset tasks instead of simply copying
sh "${labpath}/constructMonitor.sh" "/home/data/NDClab/datasets/${project}" $filetypes $tasks
# sets up hallMonitor sub file without any default mapping or replacement
cp "${labpath}/template/hallMonitor.sub" "${project}/${datam_path}"

echo "Setting up preprocess.sub"
cp "${labpath}/template/preprocess.sub" "${project}/${datam_path}"