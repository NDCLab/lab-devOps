#!/bin/bash

# A script to set up paths and environment configs to lab technicians environment

# Cron jobs to install. Describes the following:
# update-repo: manually update all repositories
# clean-logs: clean up logs if too large
# verify-encrpytion: verify that all sensitive data files are encrypted
# check-hpc-status: check if cpu usage is too high
# backup: backup all data folders by creating softlinks
crontab -l | { cat; echo "0 7 * * * /home/data/NDClab/tools/lab-devOps/scripts/updates/update-repo.sh > /home/data/NDClab/other/logs/repo-updates/"\`date +"\\%m_\\%d_\\%Y::\\%H:\\%M:\\%S"\`".log 2>&1"; } | crontab -
crontab -l | { cat; echo "0 7 1 1 * /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh /home/data/NDClab/other/logs > /home/data/NDClab/other/logs/clean-up/"\`date +"\\%m_\\%d_\\%Y::\\%H:\\%M:\\%S"\`".log 2>&1"; } | crontab -
crontab -l | { cat; echo "0 7 3 7 * /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh /home/data/NDClab/other/logs > /home/data/NDClab/other/logs/clean-up/"\`date +"\\%m_\\%d_\\%Y::\\%H:\\%M:\\%S"\`".log 2>&1"; } | crontab -
crontab -l | { cat; echo "0 7 * * * /home/data/NDClab/tools/lab-devOps/scripts/compl/verify-encryption.sh > /home/data/NDClab/other/logs/encrypt-checks/"\`date +"\\%m_\\%d_\\%Y::\\%H:\\%M:\\%S"\`".log 2>&1"; } | crontab -
crontab -l | { cat; echo "*/10 0 * * * /home/data/NDClab/tools/lab-devOps/scripts/backup/backup.sh > /home/data/NDClab/other/logs/backups/"\`date +"\\%m_\\%d_\\%Y::\\%H:\\%M:\\%S"\`".log 2>&1"; } | crontab -

# add umask

echo 'umask u+x' >> ~/.bashrc
echo 'cd /home/data/NDClab' >> ~/.bashrc
