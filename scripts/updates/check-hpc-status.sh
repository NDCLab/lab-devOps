#!/bin/bash
# A script to update the status of the hpc to the wiki. Made to be run using cron.

hour=$(date +%H)
cutoff=60.00

runtime=$(date +"%m_%d_%Y::%H:%M:%S")
file_name="${runtime}.txt"

sar -s "${hour}:00:00" -u > $file_name

array=$(grep '^Average' $file_name)
split_arr=($array)
percent=${split_arr[${#split_arr[@]}-1]}

rm -f $file_name

if (( $(echo "$percent < $cutoff" |bc -l) ))
then
    echo "Less than cutoff, updating."
    sed -i 's/HPC login node at normal usage./HPC login node idle CPU-time is less than 60%. Expect slowness./' /home/data/NDClab/tools/wiki/docs/hpc/status.md
    sed -i 's/green/red/' /home/data/NDClab/tools/wiki/docs/hpc/status.md
else
    echo "Normal usage."
    sed -i 's/HPC login node idle CPU-time is less than 60%. Expect slowness./HPC login node at normal usage./' /home/data/NDClab/tools/wiki/docs/hpc/status.md
    sed -i 's/red/green/' /home/data/NDClab/tools/wiki/docs/hpc/status.md
fi

# commit changes in wiki to branch if they exist
if [[ `git status --porcelain` ]]; then
    echo "status.md updated, pushing"
    cd /home/data/NDClab/tools/wiki/docs/hpc
    git add status.md
    git commit -m "Updated hpc status"
    git push
else
   echo "nothing to push"
fi
