#!/bin/bash
# A script to lock group out of project folder

# USAGE: make-private </data/path>
usage() { echo "Usage: sh make-private.sh </data/path>" 1>&2; exit 1; }

if [ ! -d $1 ] 
then
    echo "Directory $1 does not exist. Please check path." 
    exit 9999 
fi

setfacl -Rm d:g::---,g::--- $1
setfacl -Rm d:o::---,o::--- $1

echo "Group is locked out of $1" 
getfacl $1