#!/bin/bash
# A script to list all project permissions for a list of users and/or projects

usage() {
  cat <<EOF
  Usage: $0 [-u user1,user2,user3] [-p project1,project2,project3] [-a] [-d]

  -u list permissions for a list of users
  -p list permissions for a list of projects
  -a print all permissions on all projects
  -d include default permissions

EOF
exit 0
}

#IFS=$'\n'
DATA_PATH=/home/data/NDClab/datasets
TOOL_PATH=/home/data/NDClab/tools
ANA_PATH=/home/data/NDClab/analyses

while getopts ":u:p:ad" opt; do
  case "${opt}" in
    u)
      users=${OPTARG}
      users=${users//,/ }
      aud_users=true
      ;;
    p)
      proj=${OPTARG}
      proj=${proj//,/ }
      aud_proj=true
      ;;
    a)
      aud_all=true
      ;;
    d)
      d_flag="-d"
      ;;
    *)
      usage
      ;;
  esac
done


if [[ $aud_all == true ]]; then aud_users=false && aud_proj=false; fi

if [[ $aud_proj == true ]]
  then
  echo "Displaying user permissions for the projects: ${proj[@]}"
  for dir in ${DATA_PATH} ${TOOL_PATH} ${ANA_PATH}
    do
    for project in $(ls $dir)
      do
      if [[ "${proj[*]}" =~ "$project" ]];
        then
        IFS=$'\n' acl=($(getfacl -p -a $d_flag $dir/$project | grep "user")) && unset IFS
        printf "The project \"$project\" in \"$(basename $dir)\" has the permissions:\n"
        printf "\t%s\n" "${acl[@]}" && printf "\n"
      fi
    done
  done
fi

if [[ $aud_users == true ]]
  then
  echo "Displaying permissions for the users: ${users[@]}"
  for user in ${users[@]}
    do
    for dir in ${DATA_PATH} ${TOOL_PATH} ${ANA_PATH}
      do
      for project in $(ls $dir)
        do
        IFS=$'\n' acl=($(getfacl -p -a $d_flag $dir/$project | grep $user)) && unset IFS
        if [[ ! ${acl[@]} == "" ]]
          then
          printf "The user \"$user\" has the permissions below in \"$(basename $dir)/$project\":\n"
          printf "\t%s\n" "${acl[@]}" && printf "\n"
        fi
      done
    done
  done
fi

if [[ $aud_all == true ]]
  then
  echo "Displaying all project permissions"
  for dir in ${DATA_PATH} ${TOOL_PATH} ${ANA_PATH}
    do
    for project in $(ls $dir)
      do
      IFS=$'\n' acl=($(getfacl -p -a $d_flag $dir/$project | grep "user")) && unset IFS
      printf "The project \"$(basename $dir)/$project\" has the permissions:\n"
      printf "\t%s\n" "${acl[@]}" && printf "\n"
    done
  done
fi
