#!/bin/bash -l

#SBATCH --nodes=1                # node count
#SBATCH --cpus-per-task=8        # CPUS to use when data parallelization

#SBATCH -A iacc_gbuzzell
#SBATCH -q highmem1
#SBATCH -p highmem1

#SBATCH --time=300:00:00          # total run time limit (HH:MM:SS)

data=$1

# load R & packages
module load gcc-8.2.0-gcc-4.8.5-sxbf4jq
module load glib-2.42.1-gcc-8.2.0-vwgomxu
module load r-4.1.2-gcc-8.2.0-bdn3iy5

# run data on one node
Rscript <SCRIPTHERE> $data
