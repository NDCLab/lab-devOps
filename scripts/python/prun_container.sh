#!/bin/bash
# A script to generate a job and submit for some python script

# USAGE: sh /home/data/NDClab/tools/lab-devOps/scripts/prun_container.sh <file_name>
usage() { echo "Usage: sh prun_container.sh <file_name> [# nodes] [walltime (in hours)]" 1>&2; exit 1; }

[[ $# -eq 0 ]] && usage

file_name=$1
# use 1 node, 1 hr walltime by default
NODES=${2:-"1"}
WALLTIME="${3:-"1"}:00:00"

if [[ "${file_name##*.}" != "py" ]]; then file_name="${file_name}".py; fi

if [[ ! -f "$file_name" ]]; then
    echo "File $file_name does not exist."
    exit 9999
fi

# Generate sub file
sub_file="${file_name%.*}.sub"

echo -e  "#!/bin/bash\\n
#SBATCH --nodes=$NODES\\n
#SBATCH --ntasks=1\\n
#SBATCH --time=$WALLTIME\\n
singularity exec /home/data/NDClab/tools/containers/python-3.9/python-3.9.simg python3 ${file_name}" >| $sub_file
# python 3.9.20

# Submit sub file
echo "Submitting $sub_file as job"
sbatch $sub_file

# Give confirmation message and instructions
echo -e "Job submitted. To rerun again, execute \\'sbatch $sub_file \\'"
