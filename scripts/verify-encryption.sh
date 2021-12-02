#!/bin/bash
IFS=$'\n'

echo "Checking repos in datasets"
for dir in `ls "/home/data/NDClab/datasets"`
do
    if [ -e "/home/data/NDClab/datasets/$dir/sourcedata/raw/zoom/" ]; then
        echo "Validating $dir encryption"
        cd "/home/data/NDClab/datasets/$dir/sourcedata/raw/zoom/"
        for sub in `ls ./`; do
            echo "checking if contents of $sub are encrypted"
            cd "$sub"
            for file in *; do
                if "gpg --list-only $file" grep -q 'gpg: encrypted with \. passphrase'; then
                    echo "file $file encrypted"
                else
                    echo "file /home/data/NDClab/datasets/$dir/sourcedata/raw/zoom/$sub/$file not encrypted, notifying tech"
                    # echo "${LOC}\$file failed encryption-check in" | mail -s "Encrypt validation failed" fsaidmur@fiu.edu
                fi
            done
        done
    fi
done
