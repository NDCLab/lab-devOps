#!/bin/bash
# A script to generate a job and submit for some matlab script

# USAGE: sh /home/data/NDClab/tools/lab-devOps/scripts/rmat.sh <file_name>
usage() { echo "Usage: sh rmat.sh <file_name> [# nodes] [walltime (in hours)] [--parallel]" 1>&2; exit 1; }


[[ $# -eq 0 ]] && usage

file_name=$1
# use 1 node, 1 hr walltime by default
NODES=${2:-"1"}
WALLTIME="${3:-"1"}:00:00"

if [[ "${file_name##*.}" != "m" ]]; then file_name="${file_name}".m; fi

if [[ ! -f "$file_name" ]]; then
    echo "File $file_name does not exist."
    exit 9999
fi

# Generate sub file
sub_file="${file_name%.*}.sub"

if [[ $* == *--parallel* ]]; then
    exec_line="matlab -nodisplay -nosplash -r ${file_name%.*}"
    cpus="4"
else
    exec_line="matlab -singleCompThread -nodisplay -nosplash -r ${file_name%.*}"
    cpus="1"
fi

MATLAB_VERSION="2023b"

echo -e "#!/bin/bash
#SBATCH --nodes=$NODES
#SBATCH --ntasks=1
#SBATCH --time=$WALLTIME
#SBATCH --cpus-per-task=${cpus} \\n
module load matlab-$MATLAB_VERSION
${exec_line}" >| $sub_file

# Submit sub file
echo "Submitting $sub_file as job"
sbatch $sub_file

# Give confirmation message and instructions
echo -e "Job submitted. To rerun again, execute \\'sbatch $sub_file \\'"
