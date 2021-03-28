#!/usr/bin/env bash
# Installs yapf for linting.

TOOLS=$(dirname ${BASH_SOURCE[0]})
LOG_NAME=setup_yapf
source ${TOOLS}/common.sh

log "Installing APT packages."
sudo apt-get -qq install -y \
    python3-virtualenv \
    python3-pip

log "Installing yapf."
(cd ${TOOLS} && \
    virtualenv -p /usr/bin/python3 venv && \
    source venv/bin/activate && \
    pip install -U yapf==0.30 && \
    deactivate)
