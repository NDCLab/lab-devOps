#!/bin/bash
# A script to recursively modify member rwX permissions for a specific project-directory.

# USAGE: group-modify <OPTIONS> </data/path> <user1>,<user2> 
# <OPTIONS>
#  -r remove to group
#  -a add to group
usage() { echo "Usage: $0 [-r] [-a] </data/path> <user1>,<user2> " 1>&2; exit 1; }

dest_path = $2
users = $3 

while getopts ":ra" opt; do
  case ${opt} in
    r )
        for ID in $(echo $users | sed "s/,/ /g")
        do
            setfacl -Rx u:ID,d:u:ID dest_path
        done
        ;;
    a )
        for ID in $(echo $users | sed "s/,/ /g")
        do
            setfacl -Rm d:u:ID:rwX,u:ID:rwX dest_path
        done
        ;;
    \? ) 
        echo "Usage: $0 [-r] [-a] </data/path> <user1>,<user2> " 1>&2; exit 1;
        ;;
    esac 
  echo "New access list of directory" 
  getfacl DEST_PATH
done


