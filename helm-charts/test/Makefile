REPO_ROOT ?= $(shell git rev-parse --show-toplevel)/
REPLICA_DIR ?= $(dir $(realpath -s $(firstword $(MAKEFILE_LIST))))/replica-sets
VERSION ?= $(shell git describe --tags --always --dirty)

$(shell mkdir -p ${REPLICA_DIR})

all: build create-rs


build:
	@echo "build"

create-rs:
	scripts/create-rs.sh


version:
	@echo ${VERSION}


clean:
	rm -rf ${REPO_ROOT}/build/

help:
	@echo REPO_ROOT    = ${REPO_ROOT}
	@echo BUILD_DIR    = ${BUILD_DIR}
	@echo VERSION      = ${VERSION}
	@grep -E '^[a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | sort

.PHONY: all build create-rs verify package publish draft-release help
