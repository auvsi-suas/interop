#!/bin/bash
# Compiles the proto definitions.

CONFIG=$(readlink -f $(dirname ${BASH_SOURCE[0]}))

set -e

(cd ${CONFIG}/../auvsi_suas/proto && protoc -I . --python_out=. *.proto)
