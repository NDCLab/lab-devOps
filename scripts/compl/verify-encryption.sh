#!/bin/bash

DATA_PATH="/home/data/NDClab/datasets"
export TOOL_PATH="/home/data/NDClab/tools/lab-devOps/scripts/configs"
LOG_PATH="/home/data/NDClab/other/logs/encrypt-checks"

paths_to_check='^(raw|checked)$'
exts_to_check='(.*mp3.*|.*mp4.*|.*m4a.*|.*wav.*|.*png.*|.*jpg.*|.*[mM]odel\.obj.*|.*[mM]odel\.mtl.*)'
LAB_USERS_TXT="/home/data/NDClab/tools/lab-devOps/scripts/configs/group.txt"
export LAB_MGR="ndclab"
export LAB_TECH=$(grep "technician" $TOOL_PATH/config-leads.json | cut -d":" -f2 | tr -d '"",')
all_files=()

function search_dir
{
    local SUBDIR=$1
    #for FILE in `find $DIR -type f \( -name "*.mp3*" -o -name "*.mp4*" \
        #-o -name "*.m4a*" -o -name "*.wav*" -o -name "*Model.jpg*" -o -name "*Model.obj*" \
        #-o -name "*.Model.mtl*" \)`; do
    #for FILE in `find $SUBDIR -type f -regextype posix-extended -regex $exts_to_check`; do
        #check_encryption "$FILE"
    find $SUBDIR -type f -regextype posix-extended -regex $exts_to_check -exec sh -c 'for f do \
        check_encryption "$f"
        done' sh {} \;
        if [[ $? == 255 ]]; then return 255; fi
}

function check_encryption
{
        local FILE="$1"
        unset ERR_FLAG
        if [[ $2 == "" ]]; then FILEPATH="$FILE"; else FILEPATH="$2"; fi
        ENCRYPT_MSG=$(gpg --list-only "$FILE" 2>&1) || ERR_FLAG=true
        if [[ "$ENCRYPT_MSG" =~ "gpg: encrypted" ]]; then
            echo "$FILE encrypted"
        elif [[ "$ENCRYPT_MSG" =~ "gpg: no valid OpenPGP data found" || "$ENCRYPT_MSG" =~ .*"packet".*"with unknown version".* ]]; then
            echo "$FILE NOT ENCRYPTED. Listing file info below:"
            getfacl "$FILE"
            PROJ_LEAD=$(grep "$DIR"\".* $TOOL_PATH/config-leads.json | cut -d":" -f2 | tr -d '"",')
            # check if project lead listed in json
            if [[ ! $PROJ_LEAD == "" ]]; then
                # email project lead on failed encryption check
                email_lead="${PROJ_LEAD}"@fiu.edu
                echo "emailing $DIR:$email_lead"
                echo "$FILEPATH is not encrypted. It must be encrypted immediately. Please contact the lab manager once corrected to confirm." | mail -s "Encrypt Check Failed in \"$DIR\"" "$email_lead"
                file_arr+=("$FILEPATH")
            else
                # can't find project lead, emailing lab mgr & lab tech
                echo "emailing $LAB_MGR & $LAB_TECH re:$DIR"
                echo "$FILEPATH is not encrypted, project lead for $DIR not found in config-leads.json" | mail -s "Encrypt Check failed in \"$DIR\"" "$LAB_MGR@fiu.edu","$LAB_TECH@fiu.edu"
                file_arr+=("$FILEPATH")
            fi
        else
            echo "New encrypt msg seen for $FILEPATH: $ENCRYPT_MSG. Listing file info below:"
            getfacl "$FILE"
            PROJ_LEAD=$(grep "$DIR"\".* $TOOL_PATH/config-leads.json | cut -d":" -f2 | tr -d '"",')
            # check if project lead listed in json
            if [[ ! $PROJ_LEAD == "" ]]; then
            # email project lead on failed encryption check
                email_lead="${PROJ_LEAD}"@fiu.edu
                echo "emailing $DIR:$email_lead"
                echo "$FILEPATH is not encrypted. It must be encrypted immediately. Please contact the lab manager once corrected to confirm. " \
                "If the file appears to be properly encrypted, contact the lab manager." | mail -s "Encrypt Check Failed in \"$DIR\"" "$email_lead"
            fi
            echo "emailing $LAB_TECH & $LAB_MGR"
            echo "New encrypt msg seen for $FILEPATH: $ENCRYPT_MSG. Follow up with project lead: ${PROJ_LEAD:-unknown}" | mail -s "Encrypt Check Failed in \"$DIR\"" "$LAB_MGR"@fiu.edu,"$LAB_TECH"@fiu.edu
            file_arr+=("$FILEPATH")
        fi
}
export -f check_encryption

echo "Checking repos in datasets"
for DIR in `ls $DATA_PATH`
do
  file_arr=()
  export DIR
  for DATA_MOD in `find $DATA_PATH/$DIR/sourcedata -maxdepth 1 -type d | cut -d"/" -f8-`
  do
    if [[ "$DATA_MOD" =~ $paths_to_check ]]; then
        echo "Validating $DIR/sourcedata/$DATA_MOD encryption"
        search_dir $DATA_PATH/$DIR/sourcedata/$DATA_MOD
        if [[ $? -eq 255 ]]; then
            echo "$PROJ_LEAD not listed in hpc_gbuzzell. Skipping $DIR" && continue 2
        fi
        while IFS= read -r -d '' ZIP; do
        #for ZIP in `find $DATA_PATH/$DIR/sourcedata/$DATA_MOD -name "*.zip"`; do
            #tmpdir="$(basename $ZIP)_tmp" # dir to extract files in zip to
            tmpdir=$(mktemp -d -p $PWD) # dir to extract files in zip to
            IFS=$'\n' zipfiles=($(unzip -l "$ZIP")) && unset IFS
            arr_len=${#zipfiles[@]}
            for i in $(seq 3 $(($arr_len-3))); do
              filename=$(echo ${zipfiles[$i]} | awk '{print $NF}')
              ext1=$(echo $filename | awk -F. '{print $(NF-1)}')
              ext2=$(echo $filename | awk -F. '{print $NF}')
              #if [[ ${exts_to_check[@]} =~ $ext1 || ${exts_to_check[@]} =~ $ext2 ]]; then
              if [[ $ext1 =~ $exts_to_check || $ext2 =~ $exts_to_check ]]; then
                unzip "$ZIP" "$filename" -d "$tmpdir"
                check_encryption "$tmpdir/$filename" "$ZIP/$filename"
                if [[ $? -eq 255 ]]; then
                    echo "$PROJ_LEAD not listed in hpc_gbuzzell. Skipping $DIR" && continue 4
                fi
              fi
              # check zips inside zip# getting convoluted but should work?
              if [[ $ext2 == "zip" ]]; then
                unzip "$ZIP" "$filename" -d "$tmpdir"
                mkdir -p "$tmpdir/${filename%.*}"
                # extract <firstzip.zip>/<secondzip.zip>/file.mp3 to tmpdir/secondzip folder
                IFS=$'\n' zipfiles2=($(unzip -l "$tmpdir/$filename")) && unset IFS
                for i in $(seq 3 $((${#zipfiles2[@]}-3))); do
                  filename2=$(echo ${zipfiles2[$i]} | awk '{print $NF}')
                  ext1=$(echo $filename2 | awk -F. '{print $(NF-1)}')
                  ext2=$(echo $filename2 | awk -F. '{print $NF}')
                  if [[ $ext1 =~ $exts_to_check || $ext2 =~ $exts_to_check ]]; then
                    unzip "$tmpdir/$filename" "$filename2" -d "$tmpdir/${filename%.*}"
                    check_encryption "$tmpdir/${filename%.*}/$filename2" "$ZIP/$filename/$filename2"
                    if [[ $? -eq 255 ]]; then
                        echo "$PROJ_LEAD not listed in hpc_gbuzzell. Skipping $DIR" && continue 5
                    fi
                  fi
                done
              fi
            done
            rm -r $tmpdir
        done < <(find $DATA_PATH/$DIR/sourcedata/$DATA_MOD -name "*.zip" -print0)
    fi
  done
  if [ "${#file_arr[@]}" -gt 0 ]
      then
      #file_arr+=("The above files in the project \"$DIR\" are not encrypted")
      # write unencrypted files to log
      printf "UNENCRYPTED: %s\n" "${file_arr[@]}"
      printf "The above files in the project \"$DIR\" are not encrypted\n"
      all_files+="${file_arr[@]}"
  fi
done

#unencrypted_files=$(echo ${file_arr[@]} | grep "UNENCRYPTED" awk '{print $2}')
# Check last week's log file
last_week=`date -d "1 days ago" +%m_%d_%Y`
for log in $(ls $LOG_PATH/$last_week* 2>/dev/null); do
    files=$(cat $log | grep "UNENCRYPTED" | awk '{print $2}')
    for file in $files; do
        if [[ "${all_files[*]}" =~ "$file" ]]; then
            # email lab mgr
            echo "$file has been unencrypted since at least $last_week" | mail -s "File still unencrypted" "$LAB_MGR@fiu.edu"
        fi
    done
done
    
