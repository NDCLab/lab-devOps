#!/bin/bash

IFS=$'\n'
TOOL_PATH="/home/data/NDClab/tools"
DATA_PATH="/home/data/NDClab/datasets"
ANA_PATH="/home/data/NDClab/analyses"
IGNORED_REPOS="rwe-dataset social-context-dataset social-context-beta-dataset social-context-gamma-dataset autism-go-academy missing-link-dataset mind-reading bug-testing-dataset"
### temporarily adding post-error-ddm, pepper to archived repos
IGNORED_REPOS+=" post-error-ddm pepper-pipeline"
###
LOG_PATH="/home/data/NDClab/other/logs/repo-updates"
LAB_MGR=$(grep "lab-manager" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
LAB_TECH=$(grep "technician" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
repoarr=()

for DIR in $TOOL_PATH $DATA_PATH $ANA_PATH
do
	echo "Checking repos in $DIR"
	for REPO in `ls $DIR`
	do
	  if [[ $IGNORED_REPOS != *"$REPO"* ]]; then
	    echo "Checking $REPO"
	    if [ -e "$DIR/$REPO/.git" ]
	      then
		cd "$DIR/$REPO"
		git fetch
		MSG=$(git pull 2>&1)
		echo $MSG # make sure to output (possible) error message to log file
		IFS=$'\n' && FILES=($(git status --porcelain)) && unset IFS
                [[ ${#FILES[@]} -gt 0 ]] && echo "Found ${#FILES[@]} modified/untracked files in $REPO"
		[[ $MSG =~ "error: Your local changes" || ${#FILES[@]} -gt 0 ]] && repoarr+=("$REPO")
	      else
		echo "Not a git repo. Skipping."
	    fi
	  else
	    echo "Skipping ignored/archived repo $REPO"
	  fi
	done
done


if [ ${#repoarr[@]} -gt 0 ]
then
    for repo in ${repoarr[@]}
    do
        PROJ_LEAD=$(grep "$repo" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
        if [[ $PROJ_LEAD == "" ]]; then
            echo "Can't find proj lead for $repo, emailing lab tech"
            echo "git status detects unpushed changes for $repo, no project lead found in config-leads.json." | mail -s \
            "$repo needs re-sync with Github" "$LAB_TECH@fiu.edu" "$LAB_MGR@fiu.edu"
        else
            # email proj lead
            echo "Emailing project lead $PROJ_LEAD for $repo"
            echo "As project lead, you are being notified that there are changes on the HPC in the $repo repo that have not " \
            "been pushed to the GitHub remote. Please identify the source of these changes and complete the git sequence to re-sync " \
            "with the GitHub remote." | mail -s "$repo needs to be re-synced with Github" "$PROJ_LEAD@fiu.edu"
        fi
    done
    # escalation after > 3 days
    last_week=`date -d "3 days ago" +%m_%d_%Y`
    for log in $(ls $LOG_PATH/$last_week* 2>/dev/null); do
        repos=($(cat $log | grep -B 1 "error: Your local changes")) # Previous line should contain name of repo
        unique_repos=()
        for line in ${repos[@]}; do
            if [[ "$line" =~ "Checking" || "$line" =~ "Found" ]]; then
                # email lab mgr
                #repo=$(echo "$line" | cut -d" " -f2)
                unique_repos+=($(echo "$line" | awk '{print $NF}'))
                unique_repos=($(echo ${unique_repos[@]} | tr ' ' '\n' | sort -u | tr '\n' ' '))
            fi
        done
        for repo in ${unique_repos[@]}; do
                PROJ_LEAD=$(grep "$repo" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
                if [[ "${repoarr[*]}" =~ "$repo" ]]; then
                    echo "$repo has not been synced with Github remote since at least $last_week. Please follow up with project lead " \
                    "${PROJ_LEAD:-\"unknown\"} about committing unsaved changes." | mail -s "$repo needs re-sync" "$LAB_MGR@fiu.edu"
                fi
        done
    done
fi
