#!/bin/bash

DATA_PATH="/home/data/NDClab/datasets"
# TODO: check check as well
ZOOM_PATH="sourcedata/raw/zoom"
AUDIO_PATH="sourcedata/raw/audio"
VID_PATH="sourcedata/raw/video"
TOOL_PATH="/home/data/NDClab/tools/lab-devOps/scripts/configs"

function verify_lead
{
    b_group=$(getent group hpc_gbuzzell)
    for i in ${b_group//,/ }
    do
        if [ $i == $1 ]; then
            echo "true" && return
        fi
    done
    echo "false"
}

echo "Checking repos in datasets"
for DIR in `ls $DATA_PATH`
do
  for DATA_MOD in "$ZOOM_PATH" "$AUDIO_PATH" "$VID_PATH"
  do
    if [ -e "$DATA_PATH/$DIR/$DATA_MOD" ]; then
        echo "Validating $DIR/$DATA_MOD encryption"
        #cd "$DATA_PATH/$DIR/$ZOOM_PATH"
        for SUB in "$DATA_PATH/$DIR/$DATA_MOD"/*; do
            echo "checking if contents of $SUB are encrypted"
            if ! [[ -x "$SUB" ]]; then
                echo "$SUB is not accessible via your permissions" 
                continue
            fi
            #cd "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB"
            file_arr=()
            for FILE in "$SUB"/*; do
                # Skip transcript files
                if [[ $FILE == *.vtt ]]; then
                    continue
                fi
                ENCRYPT_MSG=$(gpg --list-only $FILE 2>&1)
                if [[ "$ENCRYPT_MSG" =~ "gpg: encrypted with 1 passphrase" ]]; then
                    echo "$FILE encrypted"
                elif [[ "$ENCRYPT_MSG" =~ "gpg: no valid OpenPGP data found" ]]; then
                    echo "$FILE NOT ENCRYPTED. Listing file info below:"
                    getfacl $FILE
                    PROJ_LEAD=$(grep "$DIR"\".* $TOOL_PATH/config-leads.json | cut -d":" -f2 | tr -d '"",')
                    # check if listed project lead belongs to group
                    ver_result=$(verify_lead $PROJ_LEAD)
                    if [ "$ver_result" == "false" ]; then
                        echo "$PROJ_LEAD not listed in hpc_gbuzzell. Skipping $DIR"
                        continue 4
                    fi

                    file_arr+=("$FILE")
                else 
                    echo "Not applicable. Skipping"
                fi
            done
            if [ "${#file_arr[@]}" -gt 0 ]
                then
                # email project lead on failed encryption check
                email="${PROJ_LEAD}"
                echo "emailing $DIR:$email"
                file_arr+=("The above files in the project \"$DIR\" are not encrypted")
                printf "%s\n" "${file_arr[@]}" | mail -s "Encrypt Check Failed" "$email"
                # write unencrypted files to log
                printf "%s\n" "${file_arr[@]}"
            fi
        done
    fi
  done
done
