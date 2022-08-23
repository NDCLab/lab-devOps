#!/bin/bash
# A script to construct your hallMonitor file

projpath=$1
filetypes=$2
tasks=$3

# split filetypes into array
filetypes=($(echo $filetypes | tr "," "\n"))

# write out hallMonitor file with template strings
cat <<EOF >> "${projpath}/data-monitoring/hallMonitor.sh"
#!/bin/bash
IFS=$'\n'

# init proj specific variables
dataset="${projpath}"
tasks="${tasks}"
filetypes="${filetypes[@]}"
logfile="\${dataset}data-monitoring/data-monitoring-log.md"

# load in functions & variables
source /home/data/NDClab/tools/lab-devOps/scripts/monitor/tools.sh

usage() { echo "Usage: sh hallMonitor.sh [-m/-r] [string list of replacement or mapping]" 1>&2; exit 1; }

error_detected=false
for dir in \`ls \$raw\`
do
    # If pavlovia dataset
    if [ "\$dir" == "\$pavlov" ]; then
        echo "Accessing \$raw/\$dir"
        cd \$raw/\$dir

        # store dir names in array
        sub_names=(*/)
        for i in "\${!sub_names[@]}"; do
            subject=\${sub_names[\$i]}

            # check accessibility of file system
            if ! [[ -x "\$raw/\$dir/\$subject" ]]; then
                echo -e "\\t \${RED}\$subject is not accessible via your permissions\${NC} \\n" 
                continue
            fi

            # if no pavlovia dataset exists in checked, create
            if [ ! -e "\$check/\$dir" ]; then
                mkdir \$check/\$dir
            fi

            # get sub id
            id="\$(cut -d'-' -f2 <<<\$subject)"
            id=\${id::-1}

            # check if name is properly named and copy if correct
            sub_check=\$(verify_copy_sub \$subject)
            res=\$?
            if [ \$res != 0 ]; then
                echo -e "\$sub_check"
                echo -e "\\t \${RED}Error detected in \$subject. View above.\${NC} \\n" 
                error_detected=true
                continue 
            fi
            echo -e "\\t Checking files of \$raw/\$dir/\$subject"
            cd \$raw/\$dir/\$subject

            # store file names in array
            file_names=(*)
            # files_log=\$(verify_copy_pav_files "\${file_names[@]}" \$id)

            # check if files contain all tasks, appropriatley named, 
            # and contain correct ID's
            files_log=\$(verify_copy_pav_files \$id \$tasks)
            res=\$?
            if [[ \$res != 0 || "\$files_log" =~ "Error:" ]]; then
                echo -e "\$files_log"
                echo -e "\\t \${RED}Error detected in \$subject. View above\${NC} \\n"
                error_detected=true
                continue 
            else 
                echo -e "\$files_log"
                echo -e "\\t \${GREEN}Success. All data passes checks in \$subject.\${NC}"
            fi
        done
        echo -e "\\n"
        # update tracker for each id
        output=\$( python \${dataset}data-monitoring/update-tracker.py \$check"/"\$pavlov "pavlovia" )
        if [[ "\$output" =~ "Error" ]]; then
            echo -e "\\t \$output \\n \\t \${RED}Error detected in checked pavlovia data.\${NC}"
            error_detected=true
        fi
        echo \$output
        echo -e "\\n"             
    fi
    # If zoom dataset
    if [ "\$dir" == "\$zoom" ]; then
        echo "Accessing \$raw/\$dir"
        # update tracker for each id
        output=\$( python \${dataset}data-monitoring/update-tracker.py \$check"/"\$zoom "zoom" )
        if [[ "\$output" =~ "Error" ]]; then
            echo -e "\\t \$output \\n \\t \${RED}Error detected in checked zoom data.\${NC}"
            error_detected=true
            continue
        fi
        echo \$output
        echo -e "\\n"
    fi
    # If redcap dataset
    if [ "\$dir" == "\$redcap" ]; then
        echo "Accessing \$raw/\$dir"
        cd \$raw/\$dir

        # store file names in array and get most recent file, check if stem is correct
        file_name=\$( get_new_redcap )

        if [[ "\$file_name" =~ "Error:" ]]; then
            echo -e "\$file_name"
            echo -e "\\t \${RED}Error detected in \$dir. View above\${NC}"
            error_detected=true
            continue
        fi
        echo -e "\\t Newest file found: \$file_name"
        
        # move only if data does not already exist in checked
        if [ -f "\$check/\$dir/\$file_name" ]; then
            echo -e "\\t \$dir/\$file_name already exists in checked, skipping copy \\n"
            continue
        fi

        echo -e "\\t \${GREEN}Data passes criteria\${NC}"

        # if redcap does not exist in checked, create it
        if [ ! -e "\$check/\$dir" ]; then
            mkdir \$check/\$dir
        fi
        echo -e "\\t copying \$file_name to \$check/\$dir"
        cp \$raw/\$dir/\$file_name \$check/\$dir

        # rename columns in checked using replace or map
        while getopts ":rm" opt; do
            case \${opt} in
                r)
                    python \${dataset}data-monitoring/rename-cols.py \$check/\$dir/\$file_name "replace" \$2 ;;
                m)
                    python \${dataset}data-monitoring/rename-cols.py \$check/\$dir/\$file_name "map" \$2 ;;
                :)
            esac 
        done

        # update tracker
        output=\$( python \${dataset}data-monitoring/update-tracker.py \$file_name "redcap" )
        if [[ "\$output" =~ "Error" ]]; then
            echo -e "\\t \$output \\n \\t \${RED}Error detected in \$file_name.\${NC}"
            error_detected=true
            continue
        fi
        echo \$output
        echo -e "\\n"
    fi
    # EEG DATA
    # Check if file exists, duplicates, if naming convention is upheld, check if subject-id
    # check if in BIDS format, make standard of data-type stem 
    # checked needs to be in BIDS format (preprocessing?)
    # brainvision data, check 3 files (header/markers/data) (Brain Vision: .eeg, .vhdr, .vmrk)
    # define if egi or brainvision. Check if its looking for brainvision or EGI (3 standard extensions)
    # IT BIDSIFIES (bidsish)
    # preprocessing
done        

if [ \$error_detected = true ]; then
    update_log "error" \$logfile
else
    update_log "success" \$logfile
fi

EOF
