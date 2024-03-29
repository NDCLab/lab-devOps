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
      WD=$PWD
      # create initial directory structure of sourcedata/derivatives files
      cd $dpath/$dir/$backup && find * -type d -exec mkdir -p -- $backpath/$dir/$backup/{} \; &>/dev/null
      cd $WD
    fi
    IFS=$'\n' file_arr=($(find "$dpath/$dir/$backup" -type f)) && unset IFS
    for file in "${file_arr[@]}";
    do
      # extract path and filename
      orig_path=$(dirname "$file")
      filename=$(basename "$file")

      # strip original path
      path=$(echo "$orig_path" | cut -d'/' -f8-)
      echo "checking file $backpath/$dir/$backup/$path/$filename"

      # create hardlink using date and filename
      name="${filename}-link-"
      date_name="${name}`date +"%m-%d-%Y"`"
   
      echo "creating link $date_name"

      # check if last known link to file exists already
      IFS=$'\n' linked_files=($(ls "$backpath/$dir/$backup/$path/$name"* 2>/dev/null || echo "empty")) && unset IFS
      if [[ $linked_files == "empty" ]]; then
          # need parent folder to already exist to ln
          [[ ! -d "$backpath/$dir/$backup/$path" ]] && mkdir -p "$backpath/$dir/$backup/$path"
          ln "$orig_path/$filename" "$backpath/$dir/$backup/$path/$date_name"
          continue
      fi 
      for i in "${!linked_files[@]}"; do
          file_ln="${linked_files[$i]}"
          echo "checking difference of $file_ln"
          # check if it matches the contents of the original file.
          res=$(cmp --silent "$file_ln" "$orig_path/$filename" || echo "diff")
          if [[ "$res" == "" ]]; then
              echo "File exists already, skipping"
              break
          fi
      done
      if [[ "$res" == "diff" ]]; then
          # need parent folder to already exist to ln
          [[ ! -d "$backpath/$dir/$backup/$path" ]] && mkdir -p "$backpath/$dir/$backup/$path"
          ln "$orig_path/$filename" "$backpath/$dir/$backup/$path/$date_name"
      fi
    done
  done
done
