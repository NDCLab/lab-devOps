#!/bin/bash
# A script to lock group out of project folder

# USAGE: make-private </data/path>
usage() { echo "Usage: sh $1 </data/path>" 1>&2; exit 1; }

setfacl -Rm d:g::---,g::--- $3
setfacl -Rm d:o::---,o::--- $3

echo "Group is locked out of $3" 
getfacl $3