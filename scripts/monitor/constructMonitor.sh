#!/bin/bash
# A script to construct your hallMonitor file

projpath=$1
filetypes=$2
tasks=$3
ntasksdatamismatch=$4
childdata=$5
parental_reports=$6

# determine if sourcedata/raw has session folders, reproduce session+run structure in checked
#ses_re='^s[0-9]+_r[0-9]+'
#ses_names=()
#for i in $(find $projpath/sourcedata/raw -maxdepth 1 -type d); do
#  if [[ $(basename $i) =~ $ses_re ]]; then ses_names+=($(basename $i)/); fi
#done
#[[ ${#ses_names[@]} -eq 0 ]] && ses_names="none"

# write out hallMonitor file with template strings
cat <<EOF >> "${projpath}/data-monitoring/hallMonitor.sh"
#!/bin/bash
#IFS=$'\n'

# init proj specific variables
dataset="${projpath}"
tasks="${tasks}"
filetypes="${filetypes}"
ntasksdatamismatch="${ntasksdatamismatch}"
childdata="${childdata}"
parental_reports="${parental_reports}"
[[ \$ntasksdatamismatch == true ]] && ignore_mismatch_err="true"
[[ \$childdata == true ]] && childdata="true"
[[ \$parental_reports == "none" ]] && parental_reports="none"
logfile="\${dataset}/data-monitoring/data-monitoring-log.md"

# determine if sourcedata/raw has session folders, reproduce session+run structure in checked
ses_re='^s[0-9]+_r[0-9]+(_e[0-9]+)?$'
ses_names=()
for i in \$(find \$dataset/sourcedata/raw -maxdepth 1 -type d); do
  if [[ \$(basename \$i) =~ \$ses_re ]]; then ses_names+=(\$(basename \$i)/); fi
done
[[ \${#ses_names[@]} -eq 0 ]] && ses_names="none"

# load in functions & variables
source /home/data/NDClab/tools/lab-devOps/scripts/monitor/tools.sh

usage() { echo "Usage: sh hallMonitor.sh [-m/-r] [string list of replacement or mapping]" 1>&2; exit 1; }




error_detected=false
#dirs=\$(find \$raw -mindepth 1 -maxdepth 1 -type d -printf "%f ")
#unset IFS
for ses in \${ses_names[@]}
do
	[[ \$ses == "none" ]] && ses="" # if no session directories set ses to empty
	dirs=(\$(find \$raw/\$ses -mindepth 1 -maxdepth 1 -type d -printf "%f\n"))
	[[ \${dirs[*]} != *redcap* ]] && dirs+=("redcap")
	data_types=\${dirs[*]}; data_types=\${data_types// /,}
	for dir in \${dirs[@]}
	do
	    # If psychopy or pavlovia dataset
	    if [[ \${pavpsy[*]} =~ \$dir ]]; then
		echo "Accessing \$raw/\$ses\$dir"
		#cd \$raw/\$dir
		#if [ ! -e "\$check/\$dir" ]; then
		#    mkdir \$check/\$dir
		#fi
		# store dir names in array
		#sub_names=(*/)
		#sub_names=(\$(ls \$raw/\$ses\$dir))
		sub_names=(\$(find \$raw/\$ses\$dir -mindepth 1 -maxdepth 1 -type d -printf "%f\n"))
		for subject in "\${sub_names[@]}"; do
		    #subject=\${sub_names[\$i]}

		    # if no pavlovia dataset exists in checked, create
	            #if [ ! -e "\$check/\$subject/\$ses\$dir" ]; then
	            #    mkdir -p \$check/\$subject/\$ses\$dir
	            #fi

		    # check if name is properly named and copy if correct
		    sub_check=\$(verify_copy_sub \$subject \$ses\$dir)
		    res=\$?
		    if [ \$res != 0 ]; then
		        echo -e "\$sub_check"
		        echo -e "\\t \${RED}Error detected in \$subject. View above.\${NC} \\n" 
		        error_detected=true
		        continue 
		    fi
		    echo -e "\\t Checking files of \$raw/\$dir/\$subject"

		    # check if files contain all tasks, appropriatley named, 
		    # and contain correct ID's
		    files_log=\$(verify_copy_pavpsy_files \$ses\$dir \$subject \$tasks)
		    res=\$?
		    if [[ \$res != 0 || "\$files_log" =~ "Error:" ]]; then
		        echo -e "\$files_log"
		        echo -e "\\t \${RED}Error detected in \$subject. View above\${NC} \\n"
		        error_detected=true
		        continue 
		    else 
		        echo -e "\$files_log"
		        echo -e "\\t \${GREEN}Success. All Psychopy data passes checks in \$subject.\${NC}"
		    fi
		done
		echo -e "\\n"            
	    fi
	    # If zoom, audio, or video dataset
	    if [[ \${audivid[*]} =~ \$dir ]]; then
                # Audio/video files should be manually copied to checked already
		:
	    fi
	    # If redcap dataset
	    if [ "\$dir" == "redcap" ]; then
		echo "Accessing \$raw/\$ses\$dir"
		# if redcap does not exist in checked, create it
		if [ ! -e "\$check/\$dir" ]; then
		    mkdir -p \$check/\$dir
		fi

		# store file names in array and get most recent file, check if stem is correct
		redcaps=(\$( get_new_redcaps \$raw/\$ses\$dir ))
		for redcap_file in \${redcaps[@]}; do
			if [[ "\$redcap_file" =~ "Error:" ]]; then
			    echo -e "\$redcap_file"
			    echo -e "\\t \${RED}Error detected in \$dir. View above\${NC}"
			    error_detected=true
			    continue
			fi
			echo -e "\\t Newest Redcap found: \$redcap_file"
			
			# move only if data does not already exist in checked
			if [ -f "\$check/\$dir/\$redcap_file" ]; then
			    echo -e "\\t \$dir/\$redcap_file already exists in checked, skipping copy \\n"
			    continue
			fi

			echo -e "\\t \${GREEN}Data passes criteria\${NC}"


			echo -e "\\t copying \$redcap_file to \$check/\$dir"
			cp \$raw/\$ses\$dir/\$redcap_file \$check/\$dir

			# rename columns in checked using replace or map
			while getopts ":rm" opt; do
			    case \${opt} in
				r)
				    python \${dataset}/data-monitoring/rename-cols.py \$check/\$dir/\$redcap_file "replace" \$2 ;;
				m)
				    python \${dataset}/data-monitoring/rename-cols.py \$check/\$dir/\$redcap_file "map" \$2 ;;
				:)
			    esac 
			done
		done
	    fi
	    if [[ \${eegtype[*]} =~ \$dir ]]; then
		sub_names=(\$(ls \$raw/\$ses\$dir))
		for subject in "\${sub_names[@]}"; do

		# if no bidsish dataset exists in checked, create
		#if [ ! -e "\${check}/\${eeg}" ]; then
		#    mkdir \$check/\$eeg
		#fi

		#echo "Accessing \$raw/\$dir"
		#cd \$raw/\$dir
		#sub_names=(*/)
		#for i in "\${!sub_names[@]}"; do
		    #if [ ! -e "\${check}/\$subject/\$ses\$dir" ]; then
		    #    mkdir -p "\${check}/\$subject/\$ses\$dir"
		    #fi
		    #subject=\${sub_names[\$i]}
		    sub_check=\$(verify_copy_sub \$subject \$ses\$dir)
		    res=\$?
		    if [ \$res != 0 ]; then
		        echo -e "\$sub_check"
		        echo -e "\\t \${RED}Error detected in \$subject. View above.\${NC} \\n" 
		        error_detected=true
		        continue 
		    fi

		    echo -e "\\t Checking files of \$raw/\$ses\$dir/\$subject"
		    #cd \$raw/\$dir/\$subject
		    files_log=\$(verify_copy_bids_files \$ses\$dir \$subject \$tasks \$filetypes \$ignore_mismatch_err)
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
	    fi
	done

	echo "updating tracker, ses: \$ses, redcaps: \${redcaps[*]}"
        [[ \$ses == "" ]] && ses="none"
        for redcap_file in \${redcaps[@]}; do
            if [[ \$ses == "none" ]]; then
	        # update trackers
	        output=\$( python \${dataset}/data-monitoring/update-tracker.py "\${check}" \${data_types} \$dataset \$raw/redcap/\$redcap_file \$ses \$tasks \$childdata \$parental_reports)
            else
	        ses_re='^.*'\${ses:0:-1}'.*\$'
                #if [[ \$redcap_file =~ \${ses_re} ]]; then
	            output=\$( python \${dataset}/data-monitoring/update-tracker.py "\${check}" \${data_types} \$dataset \$raw/\${ses}redcap/\$redcap_file \${ses:0:-1} \$tasks \$childdata \$parental_reports)
		    echo "args: \${dataset}/data-monitoring/update-tracker.py "\${check}" \${data_types} \$dataset \$raw/\${ses}redcap/\$redcap_file \${ses:0:-1} \$tasks \$childdata \$parental_reports"
                    echo \$output
	        #fi
	    fi
        done




done

# update trackers
#output=\$( python \${dataset}/data-monitoring/update-tracker.py "\${check}" \${data_types} \$dataset \$raw/redcap/\$redcap_file \$tasks)
#        if [[ "\$output" =~ "Error" ]]; then
#            echo -e "\\t \$output \\n \\t \${RED}Error detected in checked \${data_types} data.\${NC}"
#            error_detected=true
#        fi

#cd \${dataset}/data-monitoring
if [ \$error_detected = true ]; then
    update_log "error" \$logfile
else
    update_log "success" \$logfile
fi

EOF
