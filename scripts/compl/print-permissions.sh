#!/bin/bash

BASE_PATHS=("/home/data/NDClab/datasets" "/home/data/NDClab/analyses")
SUBDIRS=("sourcedata" "derivatives")

usage() {
    echo "Usage: $0 [-u username] [-d dataset/analysis_name]"
    exit 1
}

check_user_permissions() {
    local user="$1"
    
    # Check if user exists
    if ! id "$user" &>/dev/null; then
        echo "Error: User '$user' does not exist" >&2
        exit 1
    fi
    
    echo "Non-standard permissions for user: $user"
    echo "========================================"
    
    for base_path in "${BASE_PATHS[@]}"; do
        if [[ ! -d "$base_path" ]]; then continue; fi
        
        for dataset in "$base_path"/*/; do
          dataset=$(basename "$dataset")
            
            for subdir in "${SUBDIRS[@]}"; do
                local target_dir="$base_path/$dataset/$subdir"

                if [[ ! -d "$target_dir" ]]; then continue; fi
                
                # Check if user has ACL entry with r-x or rwx
                # shellcheck disable=SC2155
                local acl_entry=$(getfacl "$target_dir" 2>/dev/null | grep "^user:$user:")
                if [[ -n "$acl_entry" ]]; then
                    # shellcheck disable=SC2155
                    local perms=$(echo "$acl_entry" | cut -d: -f3)
                    if [[ "$perms" =~ r.*x ]]; then
                        echo "$(basename "$dataset")/$subdir: $perms"
                    fi
                fi
            done
        done
    done
}

check_dataset_permissions() {
    local dataset="$1"
    
    # Check if directory exists
    if [[ ! -d "$dataset" ]]; then
        echo "Error: Directory '$dataset' does not exist" >&2
        exit 1
    fi
    
    echo "Users with access to: $dataset"
    echo "============================"
    
    for subdir in "${SUBDIRS[@]}"; do
        local target_dir="$dataset/$subdir"
        if [[ ! -d "$target_dir" ]]; then continue; fi
        
        echo "$subdir/:"
        getfacl "$target_dir" 2>/dev/null | grep "^user:" | grep -v "^user::" | while read -r line; do
            # shellcheck disable=SC2155
            local user=$(echo "$line" | cut -d: -f2)
            # shellcheck disable=SC2155
            local perms=$(echo "$line" | cut -d: -f3)
            echo "  $user: $perms"
        done
    done
}

# Parse arguments
while getopts "u:d:" opt; do
    case $opt in
        u) check_user_permissions "$OPTARG" ;;
        d) check_dataset_permissions "$OPTARG" ;;
        *) usage ;;
    esac
done

if [[ $OPTIND -eq 1 ]]; then
    usage
fi