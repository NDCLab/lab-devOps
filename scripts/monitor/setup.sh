#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup.sh [-t] [-n] [-c] [-p surv1,surv2,surv3] <project-path> [datatype1,datatype2,datatype3] [id]" 1>&2; exit 1; }

datam_path="data-monitoring"
code_path="code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"

# TODO: include ndc colors
cat << "EOF"
 .__   __.  _______   ______  __          ___      .______
 |  \ |  | |       \ /      ||  |        /   \     |   _  \
 |   \|  | |  .--.  |  ,----'|  |       /  ^  \    |  |_)  |
 |  . `  | |  |  |  |  |     |  |      /  /_\  \   |   _  <
 |  |\   | |  '--'  |  `----.|  `----./  _____  \  |  |_)  |
 |__| \__| |_______/ \______||_______/__/     \__\ |______/
EOF

echo -e "data monitoring setting up ... \\n"
sleep 2

# interpret optional t flag to construct tracker

while getopts "ncp:t" opt; do
  case "${opt}" in
    n)
      ntasksdatamismatch=true
      ;;
    c)
      childdata=true
      ;;
    p)
      parental_reports=${OPTARG}
      ;;
    t)
      gen_tracker=true
      ;;
    *)
      usage
      ;;
  esac
done
[[ -z $ntasksdatamismatch ]] && ntasksdatamismatch=false
[[ -z $childdata ]] && childdata=false
[[ -z $parental_reports ]] && parental_reports="none"

shift $((OPTIND-1))
project=$1
datatypes=$2
id=$3
if [[ $gen_tracker == true ]]; then
    echo "Setting up central tracker"
    python "${labpath}/gen-tracker.py" "${project}/${datam_path}/central-tracker_${project}.csv" $id $project
    chmod +x "${project}/${datam_path}/central-tracker_${project}.csv"
fi

# get tasks
tasks=$(python "${labpath}/get_tasks.py" "${project}/${datam_path}/data-dictionary/central-tracker_datadict.csv")
if [[ $tasks == "" ]]; then
  echo "Can't find tasks in ${project}/${datam_path}/data-dictionary/central_tracker_datadict.csv" && exit 1
else
  echo "tasks: $tasks"
fi

#TODO: loop through a list, collect list from dir.

echo "Setting up hallMonitor helper files"
# delete if previously written
if [ -f "${project}/${datam_path}/rename-cols.py" ]; then
    rm -f "${project}/${datam_path}/rename-cols.py"
fi
if [ -f "${project}/${datam_path}/update-tracker.py" ]; then
    rm -f "${project}/${datam_path}/update-tracker.py"
fi
if [ -f "${project}/${datam_path}/check-id.py" ]; then
    rm -f "${project}/${datam_path}/check-id.py"
fi
cp "${labpath}/template/rename-cols.py" "${project}/${datam_path}"
cp "${labpath}/template/update-tracker.py" "${project}/${datam_path}"
cp "${labpath}/template/check-id.py" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/rename-cols.py"
chmod +x "${project}/${datam_path}/update-tracker.py"

echo "Setting up hallMonitor.sh"
# delete if previously written
if [ -f "${project}/${datam_path}/hallMonitor.sh" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sh"
fi
if [ -f "${project}/${datam_path}/hallMonitor.sub" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sub"
fi
# set up hallMonitor sh file with preset tasks instead of simply copying
sh "${labpath}/constructMonitor.sh" "/home/data/NDClab/datasets/${project}" $datatypes $tasks $ntasksdatamismatch $childdata $parental_reports
# sets up hallMonitor sub file without any default mapping or replacement
cp "${labpath}/template/hallMonitor.sub" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/hallMonitor.sh"
chmod +x "${project}/${datam_path}/hallMonitor.sub"

echo "Setting up preprocess.sub"
# delete if previously written
if [ -f "${project}/${datam_path}/preprocess.sub" ]; then
    rm -f "${project}/${datam_path}/preprocess.sub"
fi
cp "${labpath}/template/preprocess.sub" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/preprocess.sub"
chmod +x "${project}/${datam_path}/check-id.py"
