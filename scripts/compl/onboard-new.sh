#!/bin/bash
# A script to grant read access to all lab project repos to a new team member.
# Usage: bash onboard-new.sh <username>

set -euo pipefail

usage() {
    echo "Usage: bash $0 <user1>"
    exit 0
}

if [[ $# -eq 0 ]]; then usage; fi

USERNAME="$1"

# Define key paths
BASE_PATH="/home/data/NDClab"
DATA_PATH="$BASE_PATH/datasets"
TOOL_PATH="$BASE_PATH/tools"
ANA_PATH="$BASE_PATH/analyses"

# Datasets that are open source (space-separated)
OPEN_SOURCE_REPOS="erp-core-flanker-dataset nyu-slow-flanker-dataset"

# Grant read-execute access to the base directory
setfacl -Rmd u:"$USERNAME":r-x "$BASE_PATH"
setfacl -Rm u:"$USERNAME":r-x "$BASE_PATH"

# Loop over each subdirectory under datasets, tools, and analyses
for DIR in "$DATA_PATH" "$TOOL_PATH" "$ANA_PATH"; do
    # See https://stackoverflow.com/a/2108296
    for REPO_PATH in "$DIR"/*/; do
        REPO_PATH="${REPO_PATH%/}" # Strip trailing slash
        REPO_NAME=$(basename "$REPO_PATH")

        # Set default and actual read-execute ACLs
        setfacl -Rmd u:"$USERNAME":r-x "$REPO_PATH"
        setfacl -Rm u:"$USERNAME":r-x "$REPO_PATH"

        # For private (non-open source) datasets, remove access to sourcedata and derivatives
        if [[ "$DIR" == "$DATA_PATH" ]] && [[ $OPEN_SOURCE_REPOS != *"$REPO_NAME"* ]]; then
            for SUBDIR in sourcedata derivatives; do
                TARGET="$REPO_PATH/$SUBDIR"
                if [[ -d "$TARGET" ]]; then
                    setfacl -Rmd u:"$USERNAME":--- "$TARGET"
                    setfacl -Rm u:"$USERNAME":--- "$TARGET"
                fi
            done
        fi
    done
done

echo "Access granted to user '$USERNAME'."
