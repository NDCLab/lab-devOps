#!/bin/bash
# A script to print out a user-friendly collection of folder membership.

if [ ! -d $1 ] 
then
    echo "Directory $1 does not exist. Please check path." 
    exit 9999 
fi

WRITE=$(getfacl $1 | awk '/^user:.+:rwx$/{print}')
READ=$(getfacl $1 | awk '/^user:.+:r-x$/{print}')

echo "Members who can write to folder:"
echo $WRITE

echo "Members who can read from folder:"
echo $READ
