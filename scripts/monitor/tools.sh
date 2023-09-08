#!/bin/bash

# formatting vars
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# consts of data required 

# create paths according to dataset
raw="${dataset}/sourcedata/raw"
check="${dataset}/sourcedata/checked"

# A function to update the data monitoring log markdown file. Logfile must be created before running
function update_log {
    status=$1
    logfile=$2
    if [[ ! -f "$logfile" ]]; then
        echo "$logfile does not exist, creating."
        touch $logfile
    fi
    now=`date '+%Y-%m-%d_%T'`
    echo "${now} Data monitoring status for job ${SLURM_JOB_ID}: ${status}" >> $logfile
}

# A function to get array of the newest redcap files according to redcap timestamp, not file modification date.
function get_new_redcaps {

dir=$1
if [[ -z $dir ]]; then echo "Please specify the redcaps parent folder" && exit 1; fi
redcaps=($(find $dir -type f -printf "%f\n"))
time_stamp_re='\d{4}-\d{2}-\d{2}_\d{4}'
stem_re="_DATA_${time_stamp_re}.csv$"

rc_arr=()

for i in ${redcaps[@]}; do
  stem=$(echo ${i} | grep -oP $stem_re)
  rc_arr+=(${i/$stem})
done

unique_rcs=($(for i in "${rc_arr[@]}"; do echo "$i"; done | sort -u))

for i in ${unique_rcs[@]}; do
  unset newest_time
  for j in ${redcaps[@]}; do
    if [[ "$j" == "$i"* ]]; then
      file_time=$(echo "${j}" | grep -oP "$time_stamp_re")
      if [[ $newest_time == "" || "$file_time" > "$newest_time" ]]; then
        newest_time="$file_time"
        newest_file="$j"
      fi
    fi
  done
  segment=$(echo "$newest_file" | grep -oP "$stem_re")
  if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper stem name in $newest_file, does not follow convention.${NC}"
        exit 1
  fi
  echo "$newest_file"
done
}

# function to get ID of NDC subject
function get_ID {
    subject=$1
    echo "$(cut -d'-' -f2 <<<$subject)"
}
