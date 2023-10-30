#!/bin/bash

#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --time=00:24:00          # total run time limit (HH:MM:SS)

# load python modules and execute
#module load miniconda3-4.5.11-gcc-8.2.0-oqs2mbg
#./hallMonitor.sh
module load singularity-3.8.2
singularity exec -e /home/data/NDClab/tools/containers/python-3.8/python-3.8.simg ./hallMonitor.sh

source /home/data/NDClab/tools/lab-devOps/scripts/monitor/tools.sh
logfile="data-monitoring-log.md"
NUMERRORS=$(cat slurm-${SLURM_JOB_ID}.out | grep "Error: " | wc -l)
if [[ $NUMERRORS -gt 0 ]]; then
    cat slurm-${SLURM_JOB_ID}.out | grep "Error: " > slurm-${SLURM_JOB_ID}_errorlog.out
    error_detected="true"
else
    error_detected="false"
fi
if [ $error_detected = true ]; then
    update_log "error; $NUMERRORS errors seen, check slurm-${SLURM_JOB_ID}_errorlog.out for more info" $logfile
else
    update_log "success" $logfile
fi
