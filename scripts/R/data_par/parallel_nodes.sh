#!/bin/bash -i
nodes=$1
data=$2

# chunk data into chosen nodes
Rscript split_data.R $nodes $data

for i in ${data}_chunk_*; do
    sbatch --exclude=n[086-100] /home/data/NDClab/<PATHHERE>/do_node_R.sub "$i"
done
