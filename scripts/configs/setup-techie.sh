#!/bin/bash
# A script to set up paths and environment configs to lab technicians environment

# Cron jobs to install. Describes the following:
# 
#
#
read -r -d '' mycron << EOM
0 7 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/update-repo.sh > /home/data/NDClab/other/logs/repo-updates/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
0 7 1 1 * /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh /home/data/NDClab/other/logs > /home/data/NDClab/other/logs/clean-up/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
0 7 3 7 * /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh /home/data/NDClab/other/logs > /home/data/NDClab/other/logs/clean-up/"`date +"%\m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
0 7 * * * /home/data/NDClab/tools/lab-devOps/scripts/compl/verify-encryption.sh > /home/data/NDClab/other/logs/encrypt-checks/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 9 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 10 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 11 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 12 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 13 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
30 14 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 15 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 16 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
59 17 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/check-hpc-status.sh > /home/data/NDClab/other/logs/cpu-history/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
0 0 * * 0 /home/data/NDClab/tools/lab-devOps/scripts/backup/backup.sh > /home/data/NDClab/other/logs/backups/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
0 0 * * 3 /home/data/NDClab/tools/lab-devOps/scripts/backup/backup.sh > /home/data/NDClab/other/logs/backups/"`date +"\%m_\%d_\%Y::\%H:\%M:\%S"`".log 2>&1
EOM

echo $mycron

# install crontab
# crontab $mycron