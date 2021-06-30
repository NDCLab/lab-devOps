#!/bin/bash
# A script to lock group out of project folder

# USAGE: make-private </data/path>
usage() { echo "Usage: $0 </data/path>" 1>&2; exit 1; }

dest_path = $2

setfacl -Rm d:g::---,g::--- dest_path
setfacl -Rm d:o::---,o::--- dest_path

echo "Group is locked out of $2" 
getfacl dest_path