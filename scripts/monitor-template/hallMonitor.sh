#!/bin/bash
IFS=$'\n'

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

dataset="test-readAloud-v3"
raw="/home/data/NDClab/datasets/$dataset/sourcedata/raw"
check="/home/data/NDClab/datasets/$dataset/sourcedata/checked"

pavlov="pavlovia"
redcap="redcap"
zoom="zoom"

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

function verify_copy_sub
{
    name=$1
    # check if sub name contains unexpected chars
    segment=$(echo "$name" | grep -oP "sub-[0-9]+")
    if [[ -z "$segment" ]]; then
        echo -e "\\t ${RED}Error: Improper subject name, does not follow sub-#+ convention.${NC}"
        exit 1
    fi
    if [ ! -d "$check/$dir/$name" ]; then
      echo -e "\\t Creating $check/$dir/$name"
      mkdir $check/$dir/$name
    fi
    exit 0
}

function verify_copy_pav_files
{
    elements=("$@")
    id=${elements[-1]}

    subject="sub-${id}"
    
    # unset elements[-1]
    # filter according to data file
    data=$(echo "${elements[*]}" | grep -o '.*.csv')
    last_idx=$(expr ${#elements[@]} - 1)
    
    len=$(echo "${#data[@]}")
    # check if pav folder contains more than necessary
    if [[ $len -gt 2 ]]; then
        echo -e "\\t ${RED}Error: $subject folder contains more than 2 data files."
        exit 1
    fi 

    for i in "${!data[@]}"; do
        # if last index is accessed (id), exit loop
        if [[ $i == $last_idx ]]; then
            continue
        fi

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
        if [ ! -f "$check/$dir/$subject/$file_name" ]; then
            echo -e "\\t ${GREEN}Copying $file_name to $check/$dir/$subject ${NC}"
            cp $raw/$dir/$subject/$file_name $check/$dir/$subject
        else
            echo -e "\\t $subject/$file_name already exists in checked, skipping copy"
        fi
    done

    exit 0
}


for dir in `ls $raw`
do
    # If pavlovia dataset
    if [ "$dir" == "$pavlov" ]; then
        echo "Accessing $raw/$dir"
        cd $raw/$dir

        # store dir names in array
        sub_names=(*/)
        for i in "${!sub_names[@]}"; do
            subject=${sub_names[$i]}

 	    # check accessibility of file system
	    if ! [[ -x "$raw/$dir/$subject" ]]; then
                echo -e "\\t ${RED}$subject is not accessible via your permissions${NC} \\n" 
                continue
            fi

            # if no pavlovia dataset exists in checked, create
            if [ ! -e "$check/$dir" ]; then
                mkdir $check/$dir
            fi

            # get sub id
            id="$(cut -d'-' -f2 <<<$subject)"
            id=${id::-1}

            # check if name is properly named and copy if correct
            sub_check=$(verify_copy_sub $subject)
            res=$?
            if [ $res != 0 ]; then
                echo -e "$sub_check"
                echo -e "\\t ${RED}Error detected in $subject. View above.${NC} \\n" 
                continue 
            fi
            echo -e "\\t Checking files of $raw/$dir/$subject"
            cd $raw/$dir/$subject

            # store file names in array
            file_names=(*)

            # check if files contain all tasks, appropriatley named, 
            # and contain correct ID's
            files_log=$(verify_copy_pav_files "${file_names[@]}" $id)
            res=$?
            if [[ $res != 0 || "$files_log" =~ "Error:" ]]; then
                echo -e "$files_log"
                echo -e "\\t ${RED}Error detected in $subject. View above${NC} \\n" 
                continue 
            else 
                echo -e "$files_log"
                echo -e "\\t ${GREEN}Success. All data passes checks in $subject.${NC}"
            fi
        done
        echo -e "\\n"
        # update tracker for each id
        output=$( python /home/data/NDClab/datasets/$dataset/data-monitoring/update-tracker.py $check"/"$pavlov "pavlovia" )
        if [[ "$output" =~ "Error" ]]; then
            echo -e "\\t $output \\n \\t ${RED}Error detected in checked pavlovia data.${NC}"
        fi
        echo $output
        echo -e "\\n"             
    fi
    # If zoom dataset
    if [ "$dir" == "$zoom" ]; then
        echo "Accessing $raw/$dir"
        # update tracker for each id
        output=$( python /home/data/NDClab/datasets/$dataset/data-monitoring/update-tracker.py $check"/"$zoom "zoom" )
        if [[ "$output" =~ "Error" ]]; then
            echo -e "\\t $output \\n \\t ${RED}Error detected in checked zoom data.${NC}"
            continue
        fi
        echo $output
        echo -e "\\n"
    fi
    # If redcap dataset
    if [ "$dir" == "$redcap" ]; then
        echo "Accessing $raw/$dir"
        cd $raw/$dir

        # store file names in array and get most recent file, check if stem is correct
        file_name=$( get_new_redcap )

        if [[ "$file_name" =~ "Error:" ]]; then
            echo -e "$file_name"
            echo -e "\\t ${RED}Error detected in $dir. View above${NC}"
            continue
        fi
        echo -e "\\t Newest file found: $file_name"
        
        # move only if data does not already exist in checked
        if [ -f "$check/$dir/$file_name" ]; then
            echo -e "\\t $dir/$file_name already exists in checked, skipping copy \\n"
            continue
        fi

        echo -e "\\t ${GREEN}Data passes criteria${NC}"

        # if redcap does not exist in checked, create it
        if [ ! -e "$check/$dir" ]; then
            mkdir $check/$dir
        fi
        echo -e "\\t copying $file_name to $check/$dir"
        cp $raw/$dir/$file_name $check/$dir

        # rename columns in checked using replace or map
        while getopts ":rm" opt; do
            case ${opt} in
                r)
                    python /home/data/NDClab/datasets/$dataset/data-monitoring/rename-cols.py $check/$dir/$file_name "replace" $2 ;;
                m)
                    python /home/data/NDClab/datasets/$dataset/data-monitoring/rename-cols.py $check/$dir/$file_name "map" $2 ;;
                :)
            esac 
        done

        # update tracker
        output=$( python /home/data/NDClab/datasets/$dataset/data-monitoring/update-tracker.py $file_name "redcap" )
        if [[ "$output" =~ "Error" ]]; then
            echo -e "\\t $output \\n \\t ${RED}Error detected in $file_name.${NC}"
            continue
        fi
        echo $output
        echo -e "\\n"
    fi
done        