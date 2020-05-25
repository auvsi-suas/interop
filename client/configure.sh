#!/bin/bash
# Configures the Interop Client for the Docker image build.

CLIENT=$(dirname ${BASH_SOURCE[0]})

export PYTHONPATH=$CLIENT
source ${CLIENT}/venv/bin/activate
