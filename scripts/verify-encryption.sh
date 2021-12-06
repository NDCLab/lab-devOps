#!/bin/bash
IFS=$'\n'
DATA_PATH="/home/data/NDClab/datasets"
ZOOM_PATH="sourcedata/raw/zoom"
TOOL_PATH="/home/data/NDClab/tools/lab-devOps/scripts"

function verify_lead
{
    b_group=$(getent group hpc_gbuzzell)
    for i in ${b_group//,/ }
    do
        if [ $i == $1 ]; then
            echo 0
            return 1
        fi
    done
    echo 1
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
                    echo "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB/$FILE is not encrypted" | mail -s "ENCRYPT CHECK FAILED" "$email"
                else 
                    echo "Not applicable. Skipping"
                fi
            done
        done
	echo
    fi
done
