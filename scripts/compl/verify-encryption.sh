#!/bin/bash
IFS=$'\n'
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
            exit 1
        fi
    done
    exit 0
}

echo "Checking repos in datasets"
for DIR in `ls $DATA_PATH`
do
    if [ -e "$DATA_PATH/$DIR/$ZOOM_PATH" ]; then
        echo "Validating $DIR encryption"
        cd "$DATA_PATH/$DIR/$ZOOM_PATH"
        for SUB in *; do
            echo "checking if contents of $SUB are encrypted"
            if ! [[ -x "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB" ]]; then
                echo "$SUB is not accessible via your permissions" 
                continue
            fi
            cd "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB"
            for FILE in *; do
                # Skip transcript files
                if [[ $FILE == *.vtt ]]; then
                    continue
                fi
                ENCRYPT_MSG=$(gpg --list-only $FILE 2>&1)
                if [[ "$ENCRYPT_MSG" =~ "gpg: encrypted with 1 passphrase" ]]; then
                    echo "$FILE encrypted"
                elif [[ "$ENCRYPT_MSG" =~ "gpg: no valid OpenPGP data found" ]]; then
                    echo "FILE NOT ENCRYPTED. Listing file info below:"
                    getfacl $FILE
                    PROJ_LEAD=$(grep -oP "\"$DIR\":\K.*" $TOOL_PATH/config-leads.json | tr -d '"",'| xargs)

                    # check if listed project lead belongs to group
                    ver_result=$(verify_lead $PROJ_LEAD)
                    if [ "$ver_result" == 1 ]; then
                        echo "$PROJ_LEAD not listed in hpc_gbuzzell. Exiting" 
                        exit 9999 
                    fi

                    # email project lead on failed encryption check 
                    email="${PROJ_LEAD}@fiu.edu"
                    echo "emailing $DIR:$email"
                    echo "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB/$FILE is not encrypted" | mail -s "Encrypt Check Failed" "$email"
                else 
                    echo "Not applicable. Skipping"
                fi
            done
        done
	echo
    fi
done
