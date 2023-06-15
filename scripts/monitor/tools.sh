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
bv_exts=("eeg" "vhdr" "vmrk") 
egi_exts=("mff") 
digi=("zip" "png")

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
    echo "${now} Data monitoring status: ${status}" >> $logfile
}

# A function to get array of the newest redcap files according to redcap timestamp, not file modification date.
function get_new_redcaps {

dir=$1
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
  #echo "$i"_DATA_${newest_time}.csv
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

# A function to verify if a pavlovia subject folder is named correctly. If it is, create a folder of the same name in checked.
function verify_copy_sub {
    subj=$1
    folder=$2
    # check if sub name contains unexpected chars
    segment=$(echo "$subj" | grep -oP "sub-[0-9]+")
    if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper subject name ${subj} in ${folder}, does not follow sub-#+ convention.${NC}"
        exit 1
    fi

    # create subject folder in checked directory if it doesnt exist yet
    if [ ! -d "${check}/${subj}/${folder}" ]; then
      echo -e "\\t Creating ${check}/${subj}/${folder}"
      mkdir -p ${check}/${subj}/${folder}
    fi
    exit 0
}

# A function to verify a group of pavlovia files in a subject and then copy over to respective subject folders. 
# Takes in param id and which flankers to check for
# TODO: combine with verify_bids_files
function verify_copy_pavpsy_files {
    dir=$1 
    subject=$2
    tasks=$3
    data=($(find $raw/$dir/$subject -type f -name "*.csv" -printf "%f\n"))

    # create list of tasks if relevant
    if [[ $tasks != 0 ]]; then
        tasks=($(echo ${tasks//,/ }))
        # get length of tasks
        tasklen=${#tasks[@]}
    else
        echo -e "\\t ${RED}Error: $subject folder does not contain $tasks data files."
        exit 1
    fi

    # create empty array to collect tasks observed in folder
    obs=()
    id=$(get_ID $subject)

    # filter according to data file
    len=$(echo "${#data[@]}")

    # check if folder contains exact tasks
    if [[ $len -ne $tasklen ]]; then
        echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
        exit 1
    fi

    for file_name in ${data[@]}; do
        # check if file follows naming convention according to available tasks
        presence=0
        for taskname in "${tasks[@]}"; do
            segment=$(echo "$file_name" | grep -oP "(?<=_)($taskname)")
            if [[ "$segment" ]]; then
                presence=1
                obs+=("$segment")
            fi
        done
        if [[ "$presence" == 0 ]]; then
            echo -e "\\t ${RED}Error: Improper file name $file_name, does not match any Psychopy task name from" \
	        "data-monitoring/data-dictionary/central-tracker_datadict.csv${NC}"
            continue
        fi
        # check if file contains only valid id's
        output=$( python ${dataset}/data-monitoring/check-id.py $id "${raw}/${dir}/${subject}/${file_name}" )
        if [[ "\$output" =~ "False" ]]; then
            echo -e "\\t ${RED}Error: ID mismatch in $file_name. Not equal to $id.${NC}"
            continue
        fi

        # copy file to checked if it does not exist already
        if [ ! -f "$check/$subject/$dir/$file_name" ]; then
            echo -e "\\t ${GREEN}Copying $file_name to $check/$subject/$dir ${NC}"
            cp $raw/$dir/$subject/$file_name $check/$subject/$dir
        else
            echo -e "\\t $subject/$dir/$file_name already exists in checked, skipping copy"
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
    dir=$1
    subject=$2
    tasks=$3
    filetypes=$4
    ignore_mismatch_err=$5
    files=($(find $raw/$dir/$subject -type f -printf "%f\n"))

    # create list of tasks if relevant
    if [[ $tasks != 0 ]]; then
        tasks=($(echo $tasks | tr "," "\n"))
        # get length of tasks
        tasklen=$(echo "${#tasks[@]}")
    else
        echo -e "\\t ${RED}Error: No tasks specified."
        exit 1
    fi

    # split filetypes into array
    filetypes=($(echo $filetypes | tr "," "\n"))

    # create empty array to collect tasks observed in eeg/digi folder
    obs=()
    # get sub id
    id=$(get_ID $subject)

    # search for eeg system
    if [[ $(basename $dir) == "eeg" ]]; then
        extensions=0
        for type in "${filetypes[@]}"; do
            if [[ $type == "bv" ]]; then
                extensions=("${bv_exts[@]}")
            elif [[ $type == "egi" ]]; then
                extensions=("${egi_exts[@]}")
            fi
        done
        if [ $extensions = 0 ]; then
            echo -e "\\t ${RED}Error: ${filetypes[@]} does not contain EEG files."
            exit 1
	fi
	if [[ ${filetypes[@]} == *eeg* && ${filetypes[@]} == *bv* ]]; then
	    echo -e "\\t ${RED}Error: ${filetypes[@]} should not contain both EGI and BV EEG files."
	    exit 1
        fi
    elif [[ $(basename $dir) == "digi" ]]; then
        # search for file with digi extensions
        presence=0
        for ext in "${digi[@]}"; do
            for file in "${files[@]}"; do
                encrypted_file=$(echo $file | grep ".${ext}.gpg");
                if [[ "$encrypted_file" ]]; then
                    presence=1
                    break
                fi
            done

            # if file with extension hasn't been found after iteration, exit with error
            if [[ "$presence" == 0 ]]; then
                echo -e "\\t ${RED}Error: digi folder missing $ext.gpg filetype.${NC}"
                exit 1
            else
                if [[ ! "$encrypted_file" == "" && ! -f "$check/$subject/$dir/$encrypted_file" ]]; then
                    echo -e "\\t ${RED}Can't find $encrypted_file in $check/$subject/$dir, exiting. ${NC}"
                    exit 1
                else
                    echo -e "\\t $subject/$dir/$encrypted_file already exists in checked, skipping copy"
                fi
            fi
        done
        exit 0
    fi

    # filter according to data file
    for ext in "${extensions[@]}"; do
        data=()
        for file_name in ${files[@]}; do
            [[ $file_name == *".${ext}" ]] && data+=($file_name)
        done

        len=$(echo "${#data[@]}")

        # check if folder contains exact number of tasks
        if [[ $ignore_mismatch_err == "" ]]; then
            if [[ $len -ne $tasklen ]]; then
                echo -e "\\t ${RED}Error: $subject folder does not contain $tasklen data files."
                exit 1
            fi
        else
            echo -e "\\t ${GREEN}Not checking if # tasks and # data runs are 1-to-1."
        fi
        for file_name in "${data[@]}"; do
            # check if file follows naming convention according to available tasks
            presence=0
            if [[ $ignore_mismatch_err == "" ]]; then
                for taskname in "${tasks[@]}"; do
                    segment=$(echo "$file_name" | grep -oP "(?<=_)($taskname)")
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
                if [ ! -f "$check/$subject/$dir/$file_name" ]; then
                    echo -e "\\t ${GREEN}Copying $file_name to $check/$subject/$dir ${NC}"
                    cp $raw/$dir/$subject/$file_name $check/$subject/$dir
                else
                    echo -e "\\t $subject/$dir/$file_name already exists in checked, skipping copy"
                fi
            else
                presence=1
                if [ ! -f "$check/$subject/$dir/$file_name" ]; then
                    echo -e "\\t ${GREEN}Copying $file_name to $check/$subject/$dir ${NC}"
                    cp $raw/$dir/$subject/$file_name $check/$subject/$dir
                else
                    echo -e "\\t $subject/$dir/$file_name already exists in checked, skipping copy"
                fi
            fi

        done
    done
}
