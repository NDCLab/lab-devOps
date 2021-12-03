#!/bin/bash
IFS=$'\n'
DATA_PATH="/home/data/NDClab/datasets"
ZOOM_PATH="sourcedata/raw/zoom"

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
                    PROJ_LEAD=$(grep -oP "\"$DIR\":\K.*" config-leads.json | tr -d '"",')
                    echo "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB/$FILE failed check, notifying proj. lead" | mail -s "ENCRYPT CHECK FAILED"  $PROJ_LEAD@fiu.edu
                else 
                    echo "Not applicable. Skipping"
                fi
            done
        done
	echo
    fi
done
