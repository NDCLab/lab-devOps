#!/bin/bash

# static consts given the structure of current dataset
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pavpsy=("pavlovia" "psychopy")
audivid=("zoom" "audio" "video" "digi")
eeg=("bv" "egi")

redcap="redcap"

raw="${dataset}/sourcedata/raw"
check="${dataset}/sourcedata/checked"

# A function to update the data monitoring log markdown file. Logfile must be created before running
function update_log {
    status=$1
    logfile=$2
    if [[ ! -f "$logfile" ]]; then
        echo "$logfile does not exist, creating."
        touch data-monitoring-log.md
    fi
    now=`date '+%Y-%m-%d_%T'`
    echo "${now} Data monitoring status: ${status}" >> $logfile
}

# A function to get the newest redcap file according to redcap timestamp, not file modification date.
function get_new_redcap
{
    elements=(*)
    time_stamp='\d{4}-\d{2}-\d{2}_\d{4}'
    stem="202201v0readAloudval_DATA_${time_stamp}.csv"

    # return single instance if only one file
    if [[ ${#elements[@]} == 1 ]]; then
        echo ${elements[0]}
        exit 0
    elif [[ ${#elements[@]} == 0 ]]; then
        echo -e "\\t ${RED}Error: Redcap data empty. Exiting.${NC}"
        exit 1
    fi

    # find newest file by comparing timestamp strings
    newest_file="${elements[0]}"
    newest_time=$(echo "$newest_file" | grep -oP "$time_stamp")
    for i in "${!elements[@]}"; do
        file_name="${elements[$i]}"
        file_time=$(echo "$file_name" | grep -oP "$time_stamp")
        if [[ "$file_time" > "$newest_time" ]]; then
            newest_time=$file_time
            newest_file=$file_name
        fi
    done

    # check if stem is correct
    segment=$(echo "$newest_file" | grep -oP "$stem")
    if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper stem name, does not follow convention.${NC}"
        exit 1
    fi
    echo $newest_file
}

# A function to verify if a pavlovia subject folder is named correctly. If it is, create a folder of the same name in checked.
function verify_copy_sub
{
    folder=$1
    name=$2
    # check if sub name contains unexpected chars
    segment=$(echo "$name" | grep -oP "sub-[0-9]+")
    if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper subject name, does not follow sub-#+ convention.${NC}"
        exit 1
    fi
    # copy subject over to checked directory if it doesnt exist yet
    if [ ! -d "${check}/${pavlov}/$name" ]; then
      echo -e "\\t Creating ${check}/${folder}/${name}"
      mkdir "${check}/${pavlov}/${name}"
    fi
    exit 0
}

# A function to verify a group of pavlovia files in a subject and then copy over to respective subject folders. 
# Takes in param id and which flankers to check for
function verify_copy_pavpsy_files
{
    elements=(*)
    dir=$1
    id=$2
    tasks=$3
    # create empty array to collect tasks observed in pavlovia folder
    obs=()

    subject="sub-${id}"

    # unset elements[-1]
    # filter according to data file
    data=$(echo "${elements[*]}" | grep -o '.*.csv')
    len=$(echo "${#data[@]}")

    # check if pav folder contains more than necessary
    if [[ $len -gt 2 ]]; then
        echo -e "\\t ${RED}Error: $subject folder contains more than 2 data files."
        exit 1
    fi

    for i in "${!data[@]}"; do
        file_name="${data[$i]}"

        # check if empty dir
        if [[ $file_name == "" ]]; then
            echo -e "\\t ${RED}Folder empty, skipping.${NC}"
            continue
        fi

        # select standard portion of file
        segment=$(echo "$file_name" | grep -oP "^\d+_read-aloud-val-o_s\d+_r\d+_e\d+_\d{4}-\d{2}-\d{2}_\d{2}h\d{2}\.\d{2}")
        # check if file follows naming conv
        if [[ -z "$segment" ]]; then
            echo -e "\\t ${RED}Error: Improper file name $file_name, does not meet standard${NC}"
            continue
        fi

        # check if file contains only valid id's
        # output=$( python ${dataset}data-monitoring/check-id.py $check"/"$pavlov "pavlovia" )
        """
        id_col=$(head -1 $file_name | tr ',' '\n' | cat -n | grep -w "id" | awk '{print $1}')
        mapfile -t ids < <(cat $file_name | cut -d ',' -f$id_col)
        unset ids[0]

        # ERROR HERE: temp-fix not sufficient
        for val in "${!ids[@]}"; do
            # TEMP-FIX: ids getting non-id vals, needs to be consolidated
            if ! [[ $val =~ '^[0-9]+$' ]] ; then
                continue
            fi
            if [[ ${ids[$val]} != "$id" ]]; then
                echo -e "\\t ${RED}Error: Improper id value of ${ids[$val]} in $file_name. Must equal $id ${NC}"
                break
            fi
        done
        """
        
        # extract task name if it exists, and assing to obs values
        tpat="(?<=_)(.*)(?=_s\d{1}_r\d{1}_e\d{1})"
        task=$(echo "$file_name" | grep -oP "$tpat")
        # append
        obs[${#obs[@]}]=$task

        # copy file to checked if it does not exist already
        if [ ! -f "$check/$dir/$subject/$file_name" ]; then
            echo -e "\\t ${GREEN}Copying $file_name to $check/$dir/$subject ${NC}"
            cp $raw/$dir/$subject/$file_name $check/$dir/$subject
        else
            echo -e "\\t $subject/$file_name already exists in checked, skipping copy"
        fi
    done

    # split tasks into array and compare if valid param
    if [ $tasks != 0 ]; then
        tasks=($(echo $tasks | tr "," "\n"))
        if [ "${obs[@]}" == "${tasks[@]}" ] ; then
            echo -e "\\t ${GREEN}$subject contains all required tasks ${NC}"
        else
            echo -e "\\t ${RED}Missing tasks in $subject, please make sure all tasks are included.${NC} "
        fi 
    fi

    exit 0
}
