#!/bin/bash
# A script to remove id from all datasets & analysis

# USAGE: make-private </data/path>
usage() { echo "Usage: sh remove.sh <id>" 1>&2; exit 1; }

id=$1
project=$2

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"

for dset in `ls $dpath`
do
    setfacl -Rx u:$id,d:u:$id "${dpath}/${dset}"
done

for aset in `ls $apath`
do
    setfacl -Rx u:$id,d:u:$id "${apath}/${aset}"
done
