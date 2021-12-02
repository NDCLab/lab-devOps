#!/bin/bash
IFS=$'\n'

echo "Checking repos in datasets"
for dir in `ls "/home/data/NDClab/datasets"`
do
  echo "Validating $dir encryption"
    if [ -e "/home/data/NDClab/datasets/$dir/sourcedata/raw/zoom/" ]; then
        cd "/home/data/NDClab/datasets/$dir/sourcedata/raw/zoom/"
        for sub in `ls ./`
        do
            cd "$sub"
            for file in 'ls ./'
            do
                if "gpg --list-only $file" grep -q 'gpg: encrypted with \. passphrase'; then
                    echo "file $file encrypted"
                else
                    echo "file $file not encrypted, notifying tech"
                    LOC = $(pwd)
                    echo "$file failed encryption-check in ${LOC}" | mail -s "Encrypt validation failed" fsaidmur@fiu.edu
                fi
            done
        done
    fi
done
