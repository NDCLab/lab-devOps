# Get version from pyproject.toml
VERSION := $(shell grep -oP '(?<=version = ")[^"]+' pyproject.toml | tr '.' '-')
CONTAINER := build/hm2_$(VERSION).sif

.PHONY: all clean

all: $(CONTAINER)

$(CONTAINER): Singularity.def pyproject.toml
	mkdir -p build
	sudo singularity build $(CONTAINER) Singularity.def

clean:
	rm -rf build 