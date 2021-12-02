#!/bin/bash
IFS=$'\n'
DATA_PATH="/home/data/NDClab/datasets"
ZOOM_PATH="sourcedata/raw/zoom"

echo "Checking repos in datasets"
for DIR in `ls $DATA_PATH`
do
    if [ -e "$DATA_PATH/$DIR/$ZOOM_PATH" ]; then
        echo "Validating $DIR encryption"
        if ! [[ -x "$DATA_PATH/$DIR/$ZOOM_PATH" ]]; then
            echo "$DIR is not accessible via your permissions" 
            continue
        fi
        cd "$DATA_PATH/$DIR/$ZOOM_PATH"
        for SUB in *; do
            echo "checking if contents of $SUB are encrypted"
            cd "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB"
            for FILE in *; do
                ENCRYPT_MSG=$(eval "gpg --list-only $FILE")
                if grep -q 'gpg: encrypted with . passphrase' <<< "$ENCRYPT_MSG"; then
                    echo "$FILE encrypted"
                elif grep -q 'gpg: no valid OpenPGP data found.' <<< "$ENCRYPT_MSG"; then
                    echo "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB/$FILE failed check, notifying tech"
                    # | mail -s "Encrypt validation failed" fsaidmur@fiu.edu
                else 
                    echo "Not applicable. Skipping"
                fi
            done
        done
    fi
done
