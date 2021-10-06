#!/bin/bash
# A script to print out a user-friendly collection of folder membership.

if [ ! -d $1 ] 
then
    echo "Directory $1 does not exist. Please check path." 
    exit 9999 
fi

WRITE=$(getfacl $1 | awk '/^user:.+:rwx$/||/^group:.*:rwx$/{print}')
READ=$(getfacl $1 | awk '/^user:.+:r-x$/||/^group:.*:r-x$/{print}')

printf "\nUsers & groups who can read and write to $1:\n\n"
for ID in $WRITE
do
    echo "$(echo $ID | cut -d':' -f 1-2)"
done

printf "\nUsers & groups who can only read from $1:\n\n"
for ID in $READ
do
    echo "$(echo $ID | cut -d':' -f 1-2)"
done
printf "\n"
