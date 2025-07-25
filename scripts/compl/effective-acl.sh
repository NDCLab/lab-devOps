#!/bin/bash

# Script to calculate effective ACL permissions for a given user on a file/directory
# Usage: effective-acl.sh <username> <file_or_directory>

usage() {
    echo "Usage: $0 <username> <file_or_directory>"
    echo "Example: $0 alice /home/data/NDClab/datasets/study/file.txt"
    exit 1
}

if [[ $# -ne 2 ]]; then
    usage
fi

USERNAME="$1"
TARGET="$2"

# Check if user exists
if ! id "$USERNAME" &>/dev/null; then
    echo "Error: User '$USERNAME' does not exist" >&2
    exit 1
fi

# Check if target exists
if [[ ! -e "$TARGET" ]]; then
    echo "Error: '$TARGET' does not exist" >&2
    exit 1
fi

# Get user's groups
USER_GROUPS=($(id -Gn "$USERNAME" 2>/dev/null))
if [[ ${#USER_GROUPS[@]} -eq 0 ]]; then
    echo "Error: Could not determine groups for user '$USERNAME'" >&2
    exit 1
fi

# Get ACL information
ACL_OUTPUT=$(getfacl "$TARGET" 2>/dev/null)
if [[ $? -ne 0 ]]; then
    echo "Error: Could not read ACL for '$TARGET'" >&2
    exit 1
fi

# Get file owner and group
FILE_OWNER=$(stat -c "%U" "$TARGET" 2>/dev/null)
FILE_GROUP=$(stat -c "%G" "$TARGET" 2>/dev/null)

echo "Calculating effective ACL for user '$USERNAME' on '$TARGET'"
echo "User's groups: ${USER_GROUPS[*]}"
echo "File owner: $FILE_OWNER, File group: $FILE_GROUP"
echo ""

# Function to extract permissions from ACL line
extract_permissions() {
    local acl_line="$1"
    echo "$acl_line" | cut -d: -f3
}

# Function to get effective permissions (considering mask)
get_effective_permissions() {
    local perms="$1"
    local mask="$2"
    
    if [[ -z "$mask" || "$mask" == "---" ]]; then
        echo "$perms"
        return
    fi
    
    # Apply mask to permissions (logical AND)
    local result=""
    for i in {0..2}; do
        local perm_char="${perms:$i:1}"
        local mask_char="${mask:$i:1}"
        
        if [[ "$perm_char" != "-" && "$mask_char" != "-" ]]; then
            result+="$perm_char"
        else
            result+="-"
        fi
    done
    echo "$result"
}

# Extract mask from ACL
MASK=$(echo "$ACL_OUTPUT" | grep "^mask::" | cut -d: -f3)

# Check for user-specific entry
USER_ENTRY=$(echo "$ACL_OUTPUT" | grep "^user:$USERNAME:")
if [[ -n "$USER_ENTRY" ]]; then
    USER_PERMS=$(extract_permissions "$USER_ENTRY")
    EFFECTIVE_PERMS=$(get_effective_permissions "$USER_PERMS" "$MASK")
    echo "Result: User-specific ACL entry found"
    echo "Permissions: $USER_PERMS"
    if [[ -n "$MASK" ]]; then
        echo "Mask: $MASK"
        echo "Effective permissions: $EFFECTIVE_PERMS"
    else
        echo "Effective permissions: $USER_PERMS (no mask)"
    fi
    exit 0
fi

# Check if user is the file owner
if [[ "$USERNAME" == "$FILE_OWNER" ]]; then
    OWNER_PERMS=$(echo "$ACL_OUTPUT" | grep "^user::" | cut -d: -f3)
    echo "Result: User is file owner"
    echo "Effective permissions: $OWNER_PERMS (owner permissions, not affected by mask)"
    exit 0
fi

# Check for group-specific entries
for group in "${USER_GROUPS[@]}"; do
    GROUP_ENTRY=$(echo "$ACL_OUTPUT" | grep "^group:$group:")
    if [[ -n "$GROUP_ENTRY" ]]; then
        GROUP_PERMS=$(extract_permissions "$GROUP_ENTRY")
        EFFECTIVE_PERMS=$(get_effective_permissions "$GROUP_PERMS" "$MASK")
        echo "Result: Group-specific ACL entry found for group '$group'"
        echo "Permissions: $GROUP_PERMS"
        if [[ -n "$MASK" ]]; then
            echo "Mask: $MASK"
            echo "Effective permissions: $EFFECTIVE_PERMS"
        else
            echo "Effective permissions: $GROUP_PERMS (no mask)"
        fi
        exit 0
    fi
done

# Check if user is in the file's primary group
for group in "${USER_GROUPS[@]}"; do
    if [[ "$group" == "$FILE_GROUP" ]]; then
        PRIMARY_GROUP_PERMS=$(echo "$ACL_OUTPUT" | grep "^group::" | cut -d: -f3)
        EFFECTIVE_PERMS=$(get_effective_permissions "$PRIMARY_GROUP_PERMS" "$MASK")
        echo "Result: User is member of file's primary group '$FILE_GROUP'"
        echo "Permissions: $PRIMARY_GROUP_PERMS"
        if [[ -n "$MASK" ]]; then
            echo "Mask: $MASK"
            echo "Effective permissions: $EFFECTIVE_PERMS"
        else
            echo "Effective permissions: $PRIMARY_GROUP_PERMS (no mask)"
        fi
        exit 0
    fi
done

# Fall back to 'other' permissions
OTHER_PERMS=$(echo "$ACL_OUTPUT" | grep "^other::" | cut -d: -f3)
echo "Result: Using 'other' permissions (no specific user/group entries match)"
echo "Effective permissions: $OTHER_PERMS (other permissions, not affected by mask)"

exit 0
