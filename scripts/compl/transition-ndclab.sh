#!/bin/bash

DIR="/home/data/NDClab"
GROUPNAME="hpc_gbuzzell"

# This script moves the NDCLab over to the new access management strategy.

# First, reset ACLs.
setfacl -Rbk "$DIR"

# Then, set global access restrictions. We give r-x perms to hpc_gbuzzell members, rwx to globusbksvc (HPC admin account) and gbuzzell (PI), and --- to all others.
# The mask (highest possible permissions for enumerated users/groups) is set to rwx, as we need to grant rwx to privileged users.
setfacl -Rm g:"$GROUPNAME":rx,group::rx,u:globusbksvc:rwx,u:gbuzzell:rwx,other:---,mask:rwx "$DIR"
setfacl -Rdm g:"$GROUPNAME":rx,group::rx,u:globusbksvc:rwx,u:gbuzzell:rwx,other:---,mask:rwx "$DIR"

# Then, we restrict permissions for datasets using the updated 'new-dataset.sh' script.
# This script sets null permissions (---) for the sourcedata/ and derivatives/ subdirectories (we recreate it here).
for dataset in "$DIR"/*/; do
  dataset=$(basename "$dataset")
  for protected in "sourcedata" "derivatives"; do
    if [ -d "$dataset/$protected" ]; then
      echo "Restricting access to $dataset/$protected"
      setfacl -Rm g:"$GROUPNAME":---,g::--- "$dataset/$protected"
      setfacl -Rdm g:"$GROUPNAME":---,g::--- "$dataset/$protected"
    fi
  done
done

# Finally, we restore permissions to study leads, RAs, etc. We use the official access spreadsheet to do this.

give_write_perms() {
  local DATASET="$1"
  local USER="$2"
  
  if [ ! -d "$DATASET" ]; then
    echo "$DATASET does not exist" && return 1
  fi
  if ! id "$USER" >/dev/null 2>&1; then
    echo "$USER does not exist" && return 1
  fi

  echo "Granting full access to $USER for $DATASET"
  setfacl -Rm u:"$USER":rwx "$DATASET"
  setfacl -Rdm u:"$USER":rwx "$DATASET"
}

give_read_perms() {
  local DATASET="$1"
  local USER="$2"
  
  if [ ! -d "$DATASET" ]; then
    echo "$DATASET does not exist" && return 1
  fi
  
  if ! id "$USER" >/dev/null 2>&1; then
    echo "$USER does not exist" && return 1
  fi
  
  echo "Granting read-only access to $USER for $DATASET"
  setfacl -Rm u:"$USER":rx "$DATASET"
  setfacl -Rdm u:"$USER":rx "$DATASET"
}

# Restore access for all datasets based on official access spreadsheet
echo "=== Restoring Dataset Access ==="

# abmt-r01-dataset
give_write_perms "$DIR/datasets/abmt-r01-dataset" "ostib001"

# ai-ark-dataset
give_write_perms "$DIR/datasets/ai-ark-dataset" "khoss005"
give_write_perms "$DIR/datasets/ai-ark-dataset" "llaplace"

# autism-go-academy
give_write_perms "$DIR/analyses/autism-go-academy" "khoss005"
give_write_perms "$DIR/analyses/autism-go-academy" "llaplace"

# capp-dataset
give_write_perms "$DIR/datasets/capp-dataset" "ostib001"

# casper-dataset
give_write_perms "$DIR/datasets/casper-dataset" "ostib001"
give_write_perms "$DIR/datasets/casper-dataset" "llaplace"

# diverse-hair-eeg-dataset
give_write_perms "$DIR/datasets/diverse-hair-eeg-dataset" "ostib001"
give_write_perms "$DIR/datasets/diverse-hair-eeg-dataset" "llaplace"

# emote-dataset
give_write_perms "$DIR/datasets/emote-dataset" "ostib001"
give_write_perms "$DIR/datasets/emote-dataset" "llaplace"

# erp-core-flanker-dataset
give_write_perms "$DIR/datasets/erp-core-flanker-dataset" "khoss005"
give_write_perms "$DIR/datasets/erp-core-flanker-dataset" "llaplace"
# Grant all lab members access to restricted directories
if [ -d "$DIR/datasets/erp-core-flanker-dataset/sourcedata" ]; then
    echo "Granting all lab members access to erp-core-flanker-dataset/sourcedata"
    setfacl -Rm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/erp-core-flanker-dataset/sourcedata"
    setfacl -Rdm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/erp-core-flanker-dataset/sourcedata"
fi
if [ -d "$DIR/datasets/erp-core-flanker-dataset/derivatives" ]; then
    echo "Granting all lab members access to erp-core-flanker-dataset/derivatives"
    setfacl -Rm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/erp-core-flanker-dataset/derivatives"
    setfacl -Rdm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/erp-core-flanker-dataset/derivatives"
fi

# ft-flanker-datset
give_write_perms "$DIR/datasets/ft-flanker-datset" "llaplace"

# instruments
give_write_perms "$DIR/tools/instruments" "khoss005"
give_write_perms "$DIR/tools/instruments" "llaplace"

# memory-for-error-dataset
give_write_perms "$DIR/datasets/memory-for-error-dataset" "khoss005"
give_write_perms "$DIR/datasets/memory-for-error-dataset" "llaplace"

# memory-for-error-mini
give_write_perms "$DIR/analyses/memory-for-error-mini" "khoss005"
give_write_perms "$DIR/analyses/memory-for-error-mini" "llaplace"

# memory-for-error-alpha
give_write_perms "$DIR/analyses/memory-for-error-alpha" "khoss005"
give_write_perms "$DIR/analyses/memory-for-error-alpha" "llaplace"

# mfe-online-dataset
give_write_perms "$DIR/datasets/mfe-online-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-online-dataset" "llaplace"

# mfe-c-face-dataset
give_write_perms "$DIR/datasets/mfe-c-face-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-c-face-dataset" "llaplace"

# mfe-c-object-dataset
give_write_perms "$DIR/datasets/mfe-c-object-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-c-object-dataset" "llaplace"

# mfe-d-dataset
give_write_perms "$DIR/datasets/mfe-d-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-d-dataset" "llaplace"

# mfe-e-dataset
give_write_perms "$DIR/datasets/mfe-e-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-e-dataset" "llaplace"

# mfe-feedback-dataset
give_write_perms "$DIR/datasets/mfe-feedback-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-feedback-dataset" "llaplace"
give_write_perms "$DIR/datasets/mfe-feedback-dataset" "marvazqu"

# mfe-jr-dataset
give_write_perms "$DIR/datasets/mfe-jr-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-jr-dataset" "llaplace"
give_write_perms "$DIR/datasets/mfe-jr-dataset" "anagarci"
give_write_perms "$DIR/datasets/mfe-jr-dataset" "mabrady"

# mfe-nonSoc-dataset
give_write_perms "$DIR/datasets/mfe-nonSoc-dataset" "khoss005"
give_write_perms "$DIR/datasets/mfe-nonSoc-dataset" "llaplace"

# mia-pilot-dataset
give_write_perms "$DIR/datasets/mia-pilot-dataset" "fzaki001"
give_write_perms "$DIR/datasets/mia-pilot-dataset" "llaplace"

# mind-reading
give_write_perms "$DIR/analyses/mind-reading" "khoss005"
give_write_perms "$DIR/analyses/mind-reading" "llaplace"

# nyu-slow-flanker-dataset
give_write_perms "$DIR/datasets/nyu-slow-flanker-dataset" "khoss005"
give_write_perms "$DIR/datasets/nyu-slow-flanker-dataset" "llaplace"
# Grant all lab members access to restricted directories
if [ -d "$DIR/datasets/nyu-slow-flanker-dataset/sourcedata" ]; then
    echo "Granting all lab members access to nyu-slow-flanker-dataset/sourcedata"
    setfacl -Rm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/nyu-slow-flanker-dataset/sourcedata"
    setfacl -Rdm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/nyu-slow-flanker-dataset/sourcedata"
fi
if [ -d "$DIR/datasets/nyu-slow-flanker-dataset/derivatives" ]; then
    echo "Granting all lab members access to nyu-slow-flanker-dataset/derivatives"
    setfacl -Rm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/nyu-slow-flanker-dataset/derivatives"
    setfacl -Rdm g:"$GROUPNAME":rx,group::rx "$DIR/datasets/nyu-slow-flanker-dataset/derivatives"
fi

# oops-faces-dataset
give_write_perms "$DIR/datasets/oops-faces-dataset" "emart459"
give_write_perms "$DIR/datasets/oops-faces-dataset" "llaplace"
give_write_perms "$DIR/datasets/oops-faces-dataset" "emsanche"
give_write_perms "$DIR/datasets/oops-faces-dataset" "mabonill"

# post-error-ddm
give_write_perms "$DIR/analyses/post-error-ddm" "ostib001"

# putt-putt-dataset
give_write_perms "$DIR/datasets/putt-putt-dataset" "llaplace"

# putt-putt-miss
give_write_perms "$DIR/analyses/putt-putt-miss" "llaplace"

# read-study1-dataset
give_write_perms "$DIR/datasets/read-study1-dataset" "llaplace"
give_write_perms "$DIR/datasets/read-study1-dataset" "fzaki001"
give_write_perms "$DIR/datasets/read-study1-dataset" "medinaam"

# read-study2-dataset
give_write_perms "$DIR/datasets/read-study2-dataset" "llaplace"
give_write_perms "$DIR/datasets/read-study2-dataset" "fzaki001"
give_write_perms "$DIR/datasets/read-study2-dataset" "medinaam"
give_write_perms "$DIR/datasets/read-study2-dataset" "lcruz142"
give_write_perms "$DIR/datasets/read-study2-dataset" "mabrady"
give_write_perms "$DIR/datasets/read-study2-dataset" "gmari028"
give_write_perms "$DIR/datasets/read-study2-dataset" "kavaldiv"
give_write_perms "$DIR/datasets/read-study2-dataset" "deecheva"

# read-study1
give_write_perms "$DIR/analyses/read-study1" "llaplace"
give_write_perms "$DIR/analyses/read-study1" "fzaki001"
give_write_perms "$DIR/analyses/read-study1" "medinaam"

# readAloud-valence-alpha
give_write_perms "$DIR/analyses/readAloud-valence-alpha" "llaplace"

# readAloud-valence-beta
give_write_perms "$DIR/analyses/readAloud-valence-beta" "llaplace"

# readAloud-valence-dataset
give_write_perms "$DIR/datasets/readAloud-valence-dataset" "llaplace"

# rwe-eeg-dataset
give_write_perms "$DIR/datasets/rwe-eeg-dataset" "llaplace"

# soccer-dataset
give_write_perms "$DIR/datasets/soccer-dataset" "llaplace"
give_write_perms "$DIR/datasets/soccer-dataset" "fzaki001"
give_write_perms "$DIR/datasets/soccer-dataset" "mbuch"

# social-flanker-eeg-alpha
give_write_perms "$DIR/analyses/social-flanker-eeg-alpha" "khoss005"
give_write_perms "$DIR/analyses/social-flanker-eeg-alpha" "llaplace"

# social-flanker-eeg-dataset
give_write_perms "$DIR/datasets/social-flanker-eeg-dataset" "khoss005"
give_write_perms "$DIR/datasets/social-flanker-eeg-dataset" "llaplace"

# social-ern-meta
give_write_perms "$DIR/analyses/social-ern-meta" "llaplace"

# test-dataset
give_write_perms "$DIR/datasets/test-dataset" "llaplace"

# thrive-dataset
give_write_perms "$DIR/datasets/thrive-dataset" "khoss005"
give_write_perms "$DIR/datasets/thrive-dataset" "llaplace"
give_write_perms "$DIR/datasets/thrive-dataset" "ostib001"
give_write_perms "$DIR/datasets/thrive-dataset" "anagarci"
give_write_perms "$DIR/datasets/thrive-dataset" "lcruz142"
give_write_perms "$DIR/datasets/thrive-dataset" "msuar242"
give_write_perms "$DIR/datasets/thrive-dataset" "mabrady"
give_write_perms "$DIR/datasets/thrive-dataset" "fzaki001"
give_write_perms "$DIR/datasets/thrive-dataset" "kavaldiv"
give_write_perms "$DIR/datasets/thrive-dataset" "deecheva"
# Special case for sdemirba: read access to restricted directories
give_read_perms "$DIR/datasets/thrive-dataset/sourcedata" "sdemirba"
give_read_perms "$DIR/datasets/thrive-dataset/derivatives" "sdemirba"

# thrive-theta-ddm
give_write_perms "$DIR/analyses/thrive-theta-ddm" "fzaki001"

# vmpfc-dev
give_write_perms "$DIR/analyses/vmpfc-dev" "khoss005"
give_write_perms "$DIR/analyses/vmpfc-dev" "llaplace"

# weill-nest-dataset
give_write_perms "$DIR/datasets/weill-nest-dataset" "khoss005"

# working-memory-error-dataset
give_write_perms "$DIR/datasets/working-memory-error-dataset" "fzaki001"
give_write_perms "$DIR/datasets/working-memory-error-dataset" "llaplace"

echo "=== Dataset Access Restoration Complete ==="
