#!/bin/bash
# Gives read and execute, and read write and execute permissions for specific folders within a project

usage() {
  cat <<EOF
  Usage: $0 [-u user] [-r <path/to/dir1>,<path/to/dir2>] [-w <path/to/dir1>,<path/to/dir2>]

  -u username(s) of new project member
  -r list of folders to give r+x access to (w/ full path names)
  -w list of folders to give rwx access to

EOF
exit 0
}

while getopts "u:r:w:" opt; do
  case "${opt}" in
    u)
      users=${OPTARG}
      users=${users//,/ }
      ;;
    r)
      read_dirs=${OPTARG}
      read_dirs=${read_dirs//,/ }
      ;;
    w)
      write_dirs=${OPTARG}
      write_dirs=${write_dirs//,/ }
      ;;
    *)
      usage
      ;;
  esac
done

for ID in ${users[@]}; do
  for dir in ${read_dirs[@]}; do
    echo "Giving $ID r-x access to $dir"
    find "$dir" -type d -exec setfacl -m "u:$ID:rx,d:u:$ID:rx,m:rx" {} +
  done
  for dir in ${write_dirs[@]}; do
    echo "Giving $ID rwx access to $dir"
    find "$dir" -type d -exec setfacl -m "u:$ID:rwx,d:u:$ID:rwx,m:rwx" {} +
  done
done
