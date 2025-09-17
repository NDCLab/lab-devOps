








#!/bin/bash
DIR="/home/data/NDClab"
FOLDER_TYPE="analyses" # You can change this to "datasets" or any other folder type
LOG_FILE="permission-$FOLDER_TYPE-log.txt" # Log file name based on folder type

# Redirect the output to the log file
for dataset in "$DIR/$FOLDER_TYPE"/*/; do
  dataset=${dataset%/} # Remove trailing slash
  echo "ACL for $dataset:" >> "$LOG_FILE"
  getfacl "$dataset" >> "$LOG_FILE"
  echo >> "$LOG_FILE" # Add a newline for better readability
done

