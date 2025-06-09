#!/bin/sh

# Ensure Pylance can find Node
sudo ln -sf "$(which node)" /usr/bin/node

# Set up Poetry
poetry config --local virtualenvs.in-project true
poetry install
poetry run pre-commit install

# Download and install Singularity Community Edition
export VERSION=4.3.1 &&
  wget -O /tmp/singularity.deb https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-ce_${VERSION}-jammy_amd64.deb &&
  sudo apt-get update && sudo apt-get install -y /tmp/singularity.deb &&
  rm /tmp/singularity.deb

echo "Dev Container set up successfully!"
