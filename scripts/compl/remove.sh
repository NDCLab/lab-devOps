#!/bin/bash
# A script to remove id from all datasets & analysis, or if p is specified certain datasets & analyses

# USAGE: remove [ -p <project1,project2,... ] <id>
usage() { echo "Usage: bash remove.sh [ -p <project1,project2,... ] <id>"; exit 0; }

if [[ $# -eq 0 ]]; then usage; fi

while getopts "p:" opt; do
  case "${opt}" in
    p)
      projects=${OPTARG}
      projects=${projects//,/ }
      ;;
    *)
      usage
      ;;
  esac
done

id=${@:$OPTIND:1}

dpath="/home/data/NDClab/datasets"
apath="/home/data/NDClab/analyses"
tpath="/home/data/NDClab/tools"
opath="/home/data/NDClab/other"
lpath="/home/data/NDClab/legacy"

if [[ $projects == "" ]]; then
  # remove from all repo ACL's
  for dir in $dpath $apath $tpath $opath $lpath; do
    for repo in `ls $dir`; do
      echo "removing $id from $repo"
      setfacl -Rx u:$id,d:u:$id "${dir}/${repo}"
    done
    setfacl -x u:$id,d:u:$id "${dir}"
  done
  setfacl -x u:$id,d:u:$id /home/data/NDClab
  #setfacl -Rx u:$id,d:u:$id /home/data/NDClab #alternatively
else
  for proj in $projects; do
    if [[ -d $proj ]]; then # if full path specified
      echo "removing $id from $repo"
      setfacl -Rx u:$id,d:u:$id $proj
    else
      for dir in $dpath $apath $tpath; do
        for repo in `ls $dir`; do
          if [[ "$proj" =~ .*"$repo".* ]]; then
            echo "removing $id from $repo"
            setfacl -Rx u:$id,d:u:$id "${dir}/${repo}"
          fi
        done
      done
    fi
  done
fi
