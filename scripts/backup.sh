#!/bin/bash
IFS=$'\n'
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
      echo $backpath/$dir/$backpath_name/$path/$filename
      # create hardlink
      ln $orig_path/$filename $backpath/$dir/$backpath_name/$path/"${filename}-link-`date +"%d-%m-%Y"`"
    done
  done
done
