# Scripts

This directory contians a number of useful internal lab scripts. Summary for each script is described below:

Note: It would be a good idea to add /home/data/NDClab/tools/lab-devOps/scripts/ to your path to easily execute these scripts

## make-privats.sh

A script to remove group permissions from a group

## group-modify.sh

A script to add members of the ndclab lab to be able to manipulate data within a specific dataset

## backup.sh

A script to make backups of datasets within the NDClab. Runs automatically via cron

## clean-logs.sh

A script to delete logs located within the ndc lab if it surpasses data limit

## monitor-hpc.sh

A script to monitor the cpu usage of the HPC server to time usage

## monitor-superintend.sh

Deprecated. To be removed

## print-membership.sh

A script to print the members who can manipulate data of a specific folder

## update-repo.sh

A script to automatically run on datasets to pull changes from the github

## verify-encryption.sh

A script to automatically run on datasets to verify that all data is encrpyted. 
