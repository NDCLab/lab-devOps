#!/bin/bash
# A script to grant a project lead/leads full read write access to a project.

# USAGE: bash new-project-lead.sh <user1>,<user2> <project>

set -euo pipefail

usage() {
    echo "Usage: bash $0 <user1>,<user2>,... <project>"
    exit 0
}

if [[ $# -ne 2 ]]; then usage; fi

# Parse users and project name
IFS=',' read -r -a proj_leads <<<"$1"
project="$2"

# Paths
DATA_PATH="/home/data/NDClab/datasets"
TOOL_PATH="/home/data/NDClab/tools"
ANA_PATH="/home/data/NDClab/analyses"
LAB_USERS_TXT="/home/data/NDClab/tools/lab-devOps/scripts/configs/group.txt"

# Function to verify that a user is in the group
verify_lead() {
    local lead="$1"
    IFS=',' read -r -a group_members <<<"$(cat "$LAB_USERS_TXT")"
    for member in "${group_members[@]}"; do
        if [[ "$member" == "$lead" ]]; then
            return 0
        fi
    done
    return 1
}

# Main loop
for proj_lead in "${proj_leads[@]}"; do
    if ! verify_lead "$proj_lead"; then
        echo "Error: User '$proj_lead' not found in HPC group." >&2
        exit 1
    fi

    added=false

    if [[ -d $(realpath "$project") ]]; then
        # Full path was given
        project_path=$(realpath "$project")
        echo "Granting $proj_lead rwx access to $project_path"
        setfacl -Rmd u:"$proj_lead":rwx "$project_path"
        setfacl -Rm u:"$proj_lead":rwx "$project_path"
        added=true
    else
        # Search for project by name
        for dir in "$DATA_PATH" "$TOOL_PATH" "$ANA_PATH"; do
            if [[ -d "$dir/$project" ]]; then
                echo "Granting $proj_lead rwx access to $dir/$project"
                setfacl -Rmd u:"$proj_lead":rwx "$dir/$project"
                setfacl -Rm u:"$proj_lead":rwx "$dir/$project"
                added=true
                break
            fi
        done
    fi

    if [[ "$added" == false ]]; then
        echo "Error: Project '$project' not found. '$proj_lead' was not added." >&2
        exit 2
    fi
done
