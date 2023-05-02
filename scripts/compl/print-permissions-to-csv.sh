#!/bin/bash
# Similar script to "print-permissions.sh" but prints lab permissions on each lab 
# folder into a spreasheet for easy viewing/manipulation in Excel.

IFS=$'\n'
OUT_CSV="lab_permissions.csv_`date +"%m_%d_%Y::%H:%M:%S"`"
PARENT_DIR=/home/data/NDClab

function write_to_csv
{
    echo "folder,user,permissions"
    for folder in $(find $PARENT_DIR -type d); do
        getfacl_out=($(getfacl -p $folder))
        for line in ${getfacl_out[@]}; do
            if [[ $line =~ ^user:[a-zA-Z0-9]+.*$ ]]; then
                user=$(echo $line | cut -d":" -f2)
                perm=$(echo $line | cut -d":" -f3)
                #echo "$folder,$user,$perm" >> $OUT_CSV
                echo "$folder,$user,$perm"
            fi
        done
    done
}

write_to_csv > $OUT_CSV
