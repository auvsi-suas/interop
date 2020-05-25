#!/bin/bash
# Utility scripts.

CLIENT=$(dirname ${BASH_SOURCE[0]})
REPO=${CLIENT}/..

# Quit on any error.
set -e

# Run commands from context of client directory.
cd $CLIENT

# Run the client container.
if [ "$1" == "run" ]
then
    docker run --net=host --interactive --tty auvsisuas/interop-client
fi

# Pulls new images.
if [ "$1" == "pull" ]
then
    docker pull auvsisuas/interop-client:latest
fi


# Interop developer only. Teams need not run these.


# Builds container images.
if [ "$1" == "build" ]
then
    docker build -t auvsisuas/interop-client ../ -f Dockerfile \
        --cache-from auvsisuas/interop-client:latest --pull
fi

# Tests the images.
if [ "$1" == "test" ]
then
    docker run --net="host" -it auvsisuas/interop-client bash -c \
        "export PYTHONPATH=/interop/client && \
         cd /interop/client && \
         source venv/bin/activate && \
         python3 /usr/bin/nosetests3 auvsi_suas.client && \
         deactivate && \
         source venv/bin/activate && \
         python3 /usr/bin/nosetests3 tools && \
         deactivate"
fi
