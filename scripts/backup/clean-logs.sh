#!/bin/bash
# A script to clean up log files if they surpass a size. Will be run automatically via cron.

if [ ! -d $1 ] 
then
    echo "Directory $1 does not exist. Please check path." 
    exit 9999 
fi

val=$(du -shk $1 | awk '{print $1}')
declare -i LIMIT=5000000

if [ "$val" -gt "$LIMIT" ]
  then
    echo "Log file disk usage is above $LIMIT KB. Clearing $1"
    echo "Deleting the following:"
    find $1 -name "*.log" -type f
    find $1 -name "*.log" -type f -delete
  else
    echo "Log file disk usage is $val KB. Below $LIMIT KB. Skipping."
fi
