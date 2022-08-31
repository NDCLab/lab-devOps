#!/bin/bash

# formatting vars
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# arrays containing subsets of data
pavpsy=("pavlovia" "psychopy")
audivid=("zoom" "audio" "video")
eegtype=("eeg" "digi")

# eeg system files
bv=("eeg" "vhdr" "vmrk") 
egi=("mff") 
digi=("zip" "png")

# singular variable names of data
eeg="bidsish"
redcap="redcap"

# consts of data required 

# create paths according to dataset
raw="${dataset}sourcedata/raw"
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
function get_new_redcap {
    elements=(*)
    time_stamp='\d{4}-\d{2}-\d{2}_\d{4}'
    stem="^.+_DATA_${time_stamp}.csv$"

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

# function to get ID of NDC subject
function get_ID {
    subject=$1
    # get sub id
    id="$(cut -d'-' -f2 <<<$subject)"
    id=${id::-1}
    echo $id
}

# A function to verify if a pavlovia subject folder is named correctly. If it is, create a folder of the same name in checked.
function verify_copy_sub {
    folder=$1
    name=$2
    standard=${3:-0}
    # check if sub name contains unexpected chars
    if [[ $standard == "bids" ]]; then
        segment=$(echo "$folder" | grep -oP "sub-[0-9]+")
    else
        segment=$(echo "$name" | grep -oP "sub-[0-9]+")
    fi
    
    if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper subject name ${folder}${name}, does not follow sub-#+ convention.${NC}"
        exit 1
    fi

    # copy subject over to checked directory if it doesnt exist yet
    if [ ! -d "${check}/${folder}/${name}" ]; then
      echo -e "\\t Creating ${check}/${folder}/${name}"
      mkdir "${check}/${folder}/${name}"
    fi
    exit 0
}

# A function to verify a group of pavlovia files in a subject and then copy over to respective subject folders. 
# Takes in param id and which flankers to check for
# TODO: combine with verify_bids_files
function verify_copy_pavpsy_files {
    elements=(*)
    dir=$1
    subject=$2
    tasks=$3

    # create list of tasks if relevant
    if [[ $tasks != 0 ]]; then
        tasks=($(echo $tasks | tr "," "\n"))
        # get length of tasks
        tasklen=$(echo "${#tasks[@]}")
    else
        echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
        exit 1
    fi

    # create empty array to collect tasks observed in folder
    obs=()
    id=$(get_ID $subject)

    # filter according to data file
    data=$(echo "${elements[*]}" | grep ".csv")
    data=($data)
    len=$(echo "${#data[@]}")

    # check if folder contains exact tasks
    if [[ $len -ne $tasklen ]]; then
        echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
        exit 1
    fi

    for i in "${!data[@]}"; do
        file_name="${data[$i]}"

        # check if file follows naming convention according to available tasks
        presence=0
        for taskname in "${tasks[@]}"; do
            segment=$(echo "$file_name" | grep -oP "(?<=_)($taskname)(?=(_s[a-zA-Z0-9]+_r[a-zA-Z0-9]+_e[a-zA-Z0-9]+)?_\d{4})")
            if [[ "$segment" ]]; then
                presence=1
                obs+=("$segment")
            fi
        done
        if [[ "$presence" == 0 ]]; then
            echo -e "\\t ${RED}Error: Improper file name $file_name, does not meet standard${NC}"
            continue
        fi
        # check if file contains only valid id's
        output=$( python ${dataset}data-monitoring/check-id.py $id "${raw}/${dir}/${subject}${file_name}" )
        if [[ "\$output" =~ "False" ]]; then
            echo -e "\\t ${RED}Error: ID mismatch in $file_name. Not equal to $id.${NC}"
            continue
        fi

        # copy file to checked if it does not exist already
        if [ ! -f "$check/$dir/$subject/$file_name" ]; then
            echo -e "\\t ${GREEN}Copying $file_name to $check/$dir/$subject ${NC}"
            cp $raw/$dir/$subject/$file_name $check/$dir/$subject
        else
            echo -e "\\t $subject/$file_name already exists in checked, skipping copy"
        fi

    done

    # compare tasks found to tasks required
    if [[ $tasks != 0 ]]; then
        # find difference between two arrays, if 0, contains all tasks
        diff=(`echo ${obs[@]} ${tasks[@]} | tr ' ' '\n' | sort | uniq -u `)
        if [[ ${#diff[@]} -eq 0 ]] ; then
            echo -e "\\t ${GREEN}$subject contains all required tasks ${NC}"
        else
            echo -e "\\t ${RED}Error: Missing tasks in $subject, only found ${obs[@]}. ${tasks[@]} required instead. ${NC} "
            exit 1
        fi 
    fi

    exit 0
}

function verify_copy_bids_files {
    elements=(*)
    dir=$1
    subject=$2
    tasks=$3

    # create list of tasks if relevant
    if [[ $tasks != 0 ]]; then
        tasks=($(echo $tasks | tr "," "\n"))
        # get length of tasks
        tasklen=$(echo "${#tasks[@]}")
    else
        echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
        exit 1
    fi

    # create empty array to collect tasks observed in pavlovia folder
    obs=()
    # get sub id
    id=$(get_ID $subject)

    # search for eeg system
    if [[ $dir == "eeg" ]]; then
        for taskname in "${tasks[@]}"; do
            if [[ $taskname == "bv" ]]; then
                extensions=$bv
            elif [[ $taskname == "egi" ]]; then
                extensions=$egi
            fi
        done
    elif [[ $dir == "digi" ]]; then
        # TODO: unravel loop (function?)
        for ext in "${digi[@]}"; do
            file=$(echo "${elements[*]}" | grep "\.${ext}")
            if [[ -z "$file" ]]; then
                echo -e "\\t ${RED}Error: digi folder missing $ext filetype.${NC}"
                exit 1
            fi
        done
        # copy file to checked if it does not exist already
        if [ ! -f "$check/$eeg/$subject/$dir/$file_name" ]; then
            echo -e "\\t ${GREEN}Copying $file_name to $check/$eeg/$subject/$dir ${NC}"
            cp $raw/$dir/$subject/$file_name $check/$eeg/$subject/$dir
        else
            echo -e "\\t $subject/$dir/$file_name already exists in checked, skipping copy"
        fi
    fi

    # filter according to data file
    for ext in "${extensions[@]}"; do
        data=$(echo "${elements[*]}" | grep "\.${ext}")
        data=($data)
        len=$(echo "${#data[@]}")

        # check if folder contains exact number of tasks
        if [[ $len -ne $tasklen ]]; then
            echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
            exit 1
        fi

        for i in "${!data[@]}"; do
            file_name="${data[$i]}"

            # check if file follows naming convention according to available tasks
            presence=0
            for taskname in "${tasks[@]}"; do
                segment=$(echo "$file_name" | grep -oP "(?<=$subject_)($taskname)(?=*_s[a-zA-Z0-9]+_r[a-zA-Z0-9]+_e[a-zA-Z0-9]+)")
                if [[ "$segment" ]]; then
                    presence=1
                    obs+=("$segment")
                fi
            done
            if [[ "$presence" == 0 ]]; then
                echo -e "\\t ${RED}Error: Improper file name $file_name, does not meet standard${NC}"
                continue
            fi

            # copy file to checked if it does not exist already
            if [ ! -f "$check/$eeg/$subject/$dir/$file_name" ]; then
                echo -e "\\t ${GREEN}Copying $file_name to $check/$eeg/$subject/$dir ${NC}"
                cp $raw/$dir/$subject/$file_name $check/$eeg/$subject/$dir
            else
                echo -e "\\t $subject/$dir/$file_name already exists in checked, skipping copy"
            fi

        done
    done

    exit 0
}