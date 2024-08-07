#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup.sh [-t] [-c] <project-name>" 1>&2; exit 1; }

datam_path="data-monitoring"
code_path="code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"
MADE_path="/home/data/NDClab/tools/lab-devOps/scripts/MADE_pipeline_standard"
datapath="/home/data/NDClab/datasets"
sing_image="/home/data/NDClab/tools/instruments/containers/singularity/inst-container.simg"
cd $datapath

module load miniconda3-4.5.11-gcc-8.2.0-oqs2mbg # needed for pandas

#include ndc colors
c1=$'\033[95m'
c2=$'\033[93m'
c3=$'\033[33m'
#c4=$'\033[34m'
c4=$'\033[94m'
c5=$'\033[92m'
ENDC=$'\033[0m'
cat <<EOF
 ${c1}.__   __.${ENDC}  ${c2}_______${ENDC}   ${c3}______${ENDC}  ${c4}__${ENDC}          ${c5}___${ENDC}      ${c2}.______${ENDC}
 ${c1}|  \ |  |${ENDC} ${c2}|       \\${ENDC} ${c3}/      |${ENDC}${c4}|  |${ENDC}        ${c5}/   \\${ENDC}     ${c2}|   _  \\${ENDC}
 ${c1}|   \|  |${ENDC} ${c2}|  .--.${ENDC}  ${c3}|  ,----'${ENDC}${c4}|  |${ENDC}       ${c5}/  ^  \\${ENDC}    ${c2}|  |_)  |${ENDC}
 ${c1}|  . \`  |${ENDC} ${c2}|  |  |${ENDC}  ${c3}|  |${ENDC}     ${c4}|  |${ENDC}      ${c5}/  /_\  \\${ENDC}   ${c2}|   _  <${ENDC}
 ${c1}|  |\   |${ENDC} ${c2}|  '--'${ENDC}  ${c3}|  \`----.${ENDC}${c4}|  \`----.${ENDC}${c5}/  _____  \\${ENDC}  ${c2}|  |_)  |${ENDC}
 ${c1}|__| \__|${ENDC} ${c2}|_______/${ENDC} ${c3}\______|${ENDC}${c4}|_______${ENDC}${c5}/__/     \__\\${ENDC} ${c2}|______/${ENDC}
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
dataset="/home/data/NDClab/datasets/${project}"
source $labpath/tools.sh
rc_dirs=$(find $raw -type d -name "redcap")
rc_arr=()
for subdir in ${rc_dirs}; do
    redcaps=($(get_new_redcaps $subdir))
    for filename in ${redcaps[@]}; do
        rc_arr+=($subdir/$filename)
    done
done
all_redcaps=$(echo ${rc_arr[*]} | sed 's/ /,/g')

if [[ $gen_tracker == true ]]; then
    echo "Setting up central tracker"
    module load singularity-3.8.2
    singularity exec --bind /home/data/NDClab/tools/lab-devOps $sing_image python3 "${labpath}/gen-tracker.py" "${project}/${datam_path}/central-tracker_${project}.csv" $project $all_redcaps
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
cp "${labpath}/template/check-datadict.py" "${project}/${datam_path}"
cp "${labpath}/template/check_existence_datatype_folders.py" "${project}/${datam_path}"
cp "${MADE_path}/subjects_yet_to_process.py" "${project}/${datam_path}"
cp "${MADE_path}/update-tracker-postMADE.py" "${project}/${datam_path}"
cp "${MADE_path}/MADE_pipeline.m" "${project}/${code_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/rename-cols.py"
chmod +x "${project}/${datam_path}/update-tracker.py"
chmod +x "${project}/${datam_path}/verify-copy.py"
chmod +x "${project}/${datam_path}/check-id.py"
chmod +x "${project}/${datam_path}/check-datadict.py"
chmod +x "${project}/${datam_path}/subjects_yet_to_process.py"
chmod +x "${project}/${datam_path}/update-tracker-postMADE.py"
chmod +x "${project}/${datam_path}/check_existence_datatype_folders.py"
chmod +x "${project}/${code_path}/MADE_pipeline.m"

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
    rm -f "${project}/${datam_path}/preprocess_wrapper.sh"
fi
cp "${labpath}/template/preprocess.sub" "${project}/${datam_path}"
cp "${labpath}/template/preprocess_wrapper.sh" "${project}/${datam_path}"


# give permissions for all copied files
chmod +x "${project}/${datam_path}/preprocess.sub"
chmod +x "${project}/${datam_path}/preprocess_wrapper.sh"
