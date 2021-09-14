#!/bin/bash
# A script to recursively modify member rwX permissions for a specific project-directory.

# USAGE: group-modify <OPTIONS> </data/path> <user1>,<user2> 
# <OPTIONS>
#  -r remove to group
#  -a add to group
usage() { echo "Usage: sh group-modify.sh [-r] [-a] </data/path> <user1>,<user2>" 1>&2; exit 1; }

while getopts ":ra" opt; do
  case ${opt} in
    r)
        for ID in $(echo $2 | sed "s/,/ /g")
        do
            setfacl -Rx u:ID,d:u:ID $1
        done ;;
    a)
        for ID in $(echo $2 | sed "s/,/ /g")
        do
            setfacl -Rm d:u:ID:rwX,u:ID:rwX $1
        done ;;
    \?) 
        echo "Usage: sh group-modify.sh [-r] [-a] </data/path> <user1>,<user2>" 1>&2; exit 1 ;;
    esac 
  echo "New access list of directory" 
  getfacl $1
done


