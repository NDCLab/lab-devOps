#!/bin/bash
# Gives read-execute and read-write-execute permissions to specified users for specified directories

set -euo pipefail

usage() {
    cat <<EOF
Usage: $0 -u <user1,user2,...> [-r <path1,path2,...>] [-w <path1,path2,...>]

Options:
  -u    Comma-separated list of usernames to grant access to
  -r    Comma-separated list of directories to grant read + execute access
  -w    Comma-separated list of directories to grant read + write + execute access
EOF
    exit 1
}

# Parse arguments
users=()
read_dirs=()
write_dirs=()

while getopts "u:r:w:" opt; do
    case "$opt" in
    u) IFS=',' read -r -a users <<<"$OPTARG" ;;
    r) IFS=',' read -r -a read_dirs <<<"$OPTARG" ;;
    w) IFS=',' read -r -a write_dirs <<<"$OPTARG" ;;
    *) usage ;;
    esac
done

if [[ ${#users[@]} -eq 0 ]]; then
    echo "Error: At least one user must be specified with -u"
    usage
fi

# Apply permissions
for user in "${users[@]}"; do
    for dir in "${read_dirs[@]:-}"; do
        if [[ -d "$dir" ]]; then
            # Set ACL for existing files
            setfacl -Rm u:"$user":r-x,u:"$user":r-x "$dir"
            # Set default ACL for new files
            setfacl -Rmd u:"$user":r-x,u:"$user":r-x "$dir"
            echo "Granted r-x access to '$dir' for user '$user'"
        else
            echo "Warning: '$dir' is not a valid directory"
        fi
    done

    for dir in "${write_dirs[@]:-}"; do
        if [[ -d "$dir" ]]; then
            setfacl -Rmd u:"$user":rwx,u:"$user":rwx "$dir"
            setfacl -Rm u:"$user":rwx,u:"$user":rwx "$dir"
            echo "Granted rwx access to '$dir' for user '$user'"
        else
            echo "Warning: '$dir' is not a valid directory"
        fi
    done
done
