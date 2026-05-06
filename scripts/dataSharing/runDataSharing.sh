#!/bin/bash

# --- Helper: Direct Input Collector ---
get_user_vars() {
    local vars=()
    echo "Please type in each instrument/variable one by one." >&2
    echo "Type 'done' when you are finished." >&2
    
    while true; do
        read -p "Variable: " item
        if [[ "${item,,}" == "done" ]]; then
            break
        fi
        if [[ -n "$item" ]]; then
            vars+=("$item")
        fi
    done

    # Join array into a comma-separated string for the --vars flag
    (IFS=,; echo "${vars[*]}")
}

# --- Main Script ---
# Define the color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color (Reset)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Data Sharing Protocol Interactive Mode${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Dataset Name
read -p "Dataset name (e.g., thrive-dataset): " DATASET_NAME
DATASET_PATH="/home/data/NDClab/datasets/$DATASET_NAME"

if [ ! -d "$DATASET_PATH" ]; then
    echo -e "${YELLOW}Warning: Dataset directory not found at $DATASET_PATH${NC}"
    read -p "Continue anyway? (y/n): " cont
    [[ "${cont,,}" != "y" ]] && exit 1
fi

# 2. Input Method
echo -e "\nHow would you like to specify instruments?"
echo "1) Use a CSV Template (--input)"
echo "2) Direct manual entry (--vars)"
read -p "Select 1 or 2: " CHOICE

CMD_ARGS="--name $DATASET_NAME --verbose"

if [ "$CHOICE" == "1" ]; then
    read -p "Enter path to CSV template: " TEMPLATE_PATH
    if [ ! -f "$TEMPLATE_PATH" ]; then
        echo -e "${YELLOW}Error: Template file not found.${NC}"
        exit 1
    fi
    CMD_ARGS="$CMD_ARGS --input $TEMPLATE_PATH"
elif [ "$CHOICE" == "2" ]; then
    VAR_LIST=$(get_user_vars)
    if [ -z "$VAR_LIST" ]; then
        echo -e "${YELLOW}Error: No variables entered.${NC}"
        exit 1
    fi
    CMD_ARGS="$CMD_ARGS --vars=$VAR_LIST"
else
    echo -e "${YELLOW}Invalid selection.${NC}"
    exit 1
fi
echo "THis is CMD_ARGS: $CMD_ARGS"
# 3. Output File
read -p "Output filename (e.g., output.xlsx): " OUTPUT_FILE
[[ "$OUTPUT_FILE" != *.xlsx ]] && OUTPUT_FILE="${OUTPUT_FILE}.xlsx"
CMD_ARGS="$CMD_ARGS --output $OUTPUT_FILE"

# --- Execution ---
echo -e "\n----------------------------------------"
echo "Constructed Command:"
echo "python dataSharing.py $CMD_ARGS"
echo "----------------------------------------"

read -p "Run this command now? (y/n): " RUN
if [[ "${RUN,,}" == "y" ]]; then
    python dataSharing.py $CMD_ARGS
else
    echo "Execution cancelled."
fi