#!/bin/bash

# USAGE: bash delete-logs.sh
# deletes all logs marked for deletion from "clean-logs-alt.sh"
usage() { echo "Usage: bash $0"; exit 0; }

if [ ! -f /home/data/NDClab/tools/lab-devOps/scripts/backup/to_be_deleted.txt ]
  then
  echo "Can't find \"to_be_deleted.txt\"." && exit 1
fi

while true; do
  cat /home/data/NDClab/tools/lab-devOps/scripts/backup/to_be_deleted.txt
  read -p "Delete all the above log files? " yn
  case $yn in
    [Yy]* ) while IFS= read -r logfile; do rm "$logfile"; done < /home/data/NDClab/tools/lab-devOps/scripts/backup/to_be_deleted.txt; break;;
    [Nn]* ) exit;;
    * ) echo "Answer yes or no.";;
  esac
done

mv "/home/data/NDClab/tools/lab-devOps/scripts/backup/to_be_deleted.txt" "/home/data/NDClab/tools/lab-devOps/scripts/backup/deleted_log_files_`date +"%m-%d-%Y"`.txt"
