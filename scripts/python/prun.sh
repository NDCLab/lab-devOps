#!/bin/bash
# A script to generate a job and submit for some python script

# USAGE: sh /home/data/NDClab/tools/lab-devOps/scripts/prun.sh <file_name>.py
usage() { echo "Usage: sh prun.sh <file_name>" 1>&2; exit 1; }

file_name=$1

if [[ ! -f "$file_name" || $file_name =~ *.py ]]; then
    echo "File $file_name does not exist or is not a py file." 
    exit 9999 
fi

# Generate sub file
sub_file="${file_name}.sub"

echo -e  "#!/bin/bash\\n
#SBATCH --nodes=1\\n
#SBATCH --ntasks=1\\n
#SBATCH --time=01:00:00\\n
module load miniconda3-4.5.11-gcc-8.2.0-oqs2mbg\\n
python ${file_name}.py" >| $sub_file

# Submit sub file
echo "Submitting $sub_file as job"
sbatch $sub_file

# Give confirmation message and instructions
echo -e "Job submitted. To rerun again, execute \\'sbatch $sub_file \\'"
