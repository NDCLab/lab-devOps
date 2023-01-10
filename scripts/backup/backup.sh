#!/bin/bash

dpath="/home/data/NDClab/datasets"
backpath="/home/data/NDClab/other/backups"
backup_list=("sourcedata" "derivatives")

for dir in `ls $dpath`
do
  echo "Checking $dir"
  if [ ! -d "$backpath/$dir" ]; then
    mkdir $backpath/$dir
  fi 

  for backup in "${backup_list[@]}" 
  do
    if [ ! -d "$backpath/$dir/$backup" ]; then
      cd $dpath/$dir/$backup && find . -type d -exec mkdir -p -- $backpath/$dir/$backup{} \;
    fi
    for file in $(find "$dpath/$dir/$backup" -type f);
    do
      # extract path and filename
      orig_path=$(dirname $file)
      filename=$(basename $file)

      # strip original path
      backpath_name="${backup}."
      path=$(echo $orig_path | cut -d'/' -f8-)
      echo "checking file $backpath/$dir/$backpath_name/$path/$filename"

      # create hardlink using date and filename
      name="${filename}-link-"
      date_name="${name}`date +"%m-%d-%Y"`"
   
      echo "creating link $date_name"

      # check if last known link to file exists already
      linked_files=($(ls $backpath/$dir/$backpath_name/$path/$name* 2>/dev/null || echo "empty"))
      if [[ $linked_files == "empty" ]]; then
          ln $orig_path/$filename $backpath/$dir/$backpath_name/$path/$date_name
          continue
      fi 
      for i in "${!linked_files[@]}"; do
          file_ln="${linked_files[$i]}"
          echo "checking difference of $file_ln"
          # check if it matches the contents of the original file.
          res=$(cmp --silent $file_ln $orig_path/$filename || echo "diff")
          if [[ "$res" == "" ]]; then
              echo "File exists already, skipping"
              break
          fi
      done
      if [[ "$res" == "diff" ]]; then
          ln $orig_path/$filename $backpath/$dir/$backpath_name/$path/$date_name
      fi
    done
  done
done
