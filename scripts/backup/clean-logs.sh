#!/bin/bash
# A script to clean up log files past six months. Will be run automatically via cron.
# USAGE: bash /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh
usage() { echo "Usage: bash $0"; exit 0; }

log_dir="/home/data/NDClab/other/logs"

# delete logs older than six months
older_than=`date -d "-12 month" +%y-%m`
find "$log_dir" -name "*.log" -exec bash -c \
  'timestamp=$(basename $1) && if [[ "${timestamp:8:2}"-"${timestamp:0:2}" < $2 ]]; \
  then echo "deleting $1" && rm $1 2>&1; fi' bash {} $older_than ';'
