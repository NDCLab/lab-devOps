#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: create-monitor.sh <project-path>" 1>&2; exit 1; }

project=$1
datam_path="/data-monitoring"
code_path="/code"

echo "Setting up hallMonitor helper files"
cp monitor-template/rename-cols.py $project
cp monitor-template/update-tracker.py $project
cp monitor-template/README.md $project
echo "Setting up hallMonitor.sh"
cp monitor-template/hallMonitor.sh $project
echo "Setting up hallMonitor.sub"
cp monitor-template/hallMonitor.sub $project

echo "Setting up preprocess.sub"
cp monitor-template/preprocess.sub $project