VERSION := $(shell grep -oP '(?<=version = ")[^"]+' pyproject.toml | tr '.' '-')
CONTAINER := build/syllable_analysis-$(VERSION).sif

.PHONY: all clean

all: $(CONTAINER)

$(CONTAINER): Singularity.def
	mkdir -p build
	sudo singularity build $(CONTAINER) Singularity.def

clean:
	rm -rf build
