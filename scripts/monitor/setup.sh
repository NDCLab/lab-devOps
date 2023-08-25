#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup.sh [-t] [-n] [-c] [-p surv1,surv2,surv3] <project-path> [datatype1,datatype2,datatype3] [id]" 1>&2; exit 1; }

datam_path="data-monitoring"
code_path="code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"

module load miniconda3-4.5.11-gcc-8.2.0-oqs2mbg # needed for pandas

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

while getopts "ct" opt; do
  case "${opt}" in
    c)
      childdata=true
      ;;
    t)
      gen_tracker=true
      ;;
    *)
      usage
      ;;
  esac
done
[[ -z $childdata ]] && childdata=false

shift $((OPTIND-1))
project=$1
id=$2
if [[ $gen_tracker == true ]]; then
    echo "Setting up central tracker"
    python "${labpath}/gen-tracker.py" "${project}/${datam_path}/central-tracker_${project}.csv" $id $project
    chmod +x "${project}/${datam_path}/central-tracker_${project}.csv"
fi

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
cp "${labpath}/template/verify-copy.py" "${project}/${datam_path}"
cp "${labpath}/template/check-id.py" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/rename-cols.py"
chmod +x "${project}/${datam_path}/update-tracker.py"
chmod +x "${project}/${datam_path}/verify-copy.py"

echo "Setting up hallMonitor.sh"
# delete if previously written
if [ -f "${project}/${datam_path}/hallMonitor.sh" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sh"
fi
if [ -f "${project}/${datam_path}/hallMonitor.sub" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sub"
fi
# set up hallMonitor sh file with preset tasks instead of simply copying
sh "${labpath}/constructMonitor.sh" "/home/data/NDClab/datasets/${project}" $childdata
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
