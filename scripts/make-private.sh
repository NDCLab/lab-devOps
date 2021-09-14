#!/bin/bash
# A script to lock group out of project folder

# USAGE: make-private </data/path>
usage() { echo "Usage: $0 </data/path>" 1>&2; exit 1; }

setfacl -Rm d:g::---,g::--- $2
setfacl -Rm d:o::---,o::--- $2

echo "Group is locked out of $2" 
getfacl $2