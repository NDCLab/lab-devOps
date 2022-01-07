#!/bin/bash
IFS=$'\n'
DATA_PATH="/home/data/NDClab/datasets"
DATA_MONIT="data-monitoring"
source_data="sourcedata"
MONIT_FILE="data-monitor.sh"
TOOL_PATH="/home/data/NDClab/tools/lab-devOps/scripts"

function verify_lead
{
    b_group=$(getent group hpc_gbuzzell)
    for i in ${b_group//,/ }
    do
        if [ $i == $1 ]; then
            echo 0
            return 1
        fi
    done
    echo 1
}

# Run through each dataset available, checking for data monitoring script
echo "Checking datasets"
for DIR in `ls $DATA_PATH`
do
    if [ -e "$DATA_PATH/$DIR/$DATA_MONIT_PATH/$MONIT_FILE" ]; then
        echo "Monitoring file present in $DIR"
        cd "$DATA_PATH/$DIR/$DATA_MONIT_PATH"

        # check data provenance status via conda datalad
        STATUS_MSG=$(conda run -n base datalad status 2>&1)

        # if no changes, simply skip dataset
        if [ "$STATUS_MSG" =~ "nothing to save, working tree clean" ]; then
            echo -e "\\t $STATUS_MSG"
            continue
        fi

        # continue by extracting and verifying project lead
        PROJ_LEAD=$(grep -oP "\"$DIR\":\K.*" $TOOL_PATH/config-leads.json | tr -d '"",'| xargs)
        ver_result=$(verify_lead $PROJ_LEAD)
        if [ "$ver_result" == 1 ]; then
            echo "$PROJ_LEAD not listed in hpc_gbuzzell. Exiting" 
            exit 9999 
        fi
        email="${PROJ_LEAD}@fiu.edu"

        # parse status message
        for item in $STATUS_MSG
        do
            # ping proj lead with instructions if file modified or deleted
            if [[ "$item" =~ "modified:" || "$item" =~ "deleted:" ]]; then
                echo "emailing $DIR:$email"
                echo "$DATA_PATH/$DIR contains modified or deleted files. If this is intentional, \
                      please execute 'datalad save'\\n $item" | mail -s "Modified or Deleted Data in $DIR" "$email"
            elif [[ "$item" =~ "untracked:" ]]; then 
                # if untracked start data-monitoring process
                monitor_result=$(sh $DATA_PATH/$DIR/$DATA_MONIT_PATH/$MONIT_FILE)
                exit_code=$?
                if [[ $exit_code == 9999 ]]; then
                    echo "emailing $DIR:$email"
                    echo "$DATA_PATH/$DIR/$source_data $monitor_result" | mail -s "Data Monitoring Failed $DIR" "$email"
                fi
                echo "emailing $DIR:$email on monitor success"
                echo "$DATA_PATH/$DIR/$source_data $monitor_result" | mail -s "Data Monitoring Succeeded $DIR" "$email"
            else
                echo "Unknown changes to dataset. Notifying tech."
            fi
        done
    fi
done