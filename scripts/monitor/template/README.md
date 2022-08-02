# HallMonitor.sub

This is a bash file to be submitted to the slurm job scheduler. It includes the following steps:

1. Verify pavlovia, update tracker, & move to checked
2. Verify redcap, update column names, update tracker, & move to checked
3. Verify zoom & update tracker

To run execute the following in your command-line:

```
sbatch hallMonitor.sub [-r/-m] [list of new columns/mapping of strings]
```

# Preprocess.sub

This is a bash file to be submitted to the slurm job scheduler. It includes the following steps:

1. Redcap preprocessing
2. Redcap data-tracking
3. R scripts preprocessing

To run execute the following in your command-line:

```
sbatch preprocess.sub [REDCAP_OUTPUT_NAME].csv
```
