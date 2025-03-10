#!/bin/bash

# Get version from pyproject.toml
VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml | tr '.' '-')

# Build the Singularity container
sudo singularity build "hm2_${VERSION}.sif" Singularity.def
