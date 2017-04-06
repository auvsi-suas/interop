#!/bin/bash
# Tests the Interop Client Docker image.

docker run --net="host" -it auvsisuas/interop-client bash -c \
    "export PYTHONPATH=/interop/client && \
     cd /interop/client && \
     source venv2/bin/activate && \
     python /usr/bin/nosetests interop && \
     deactivate && \
     source venv3/bin/activate && \
     python /usr/bin/nosetests interop && \
     deactivate && \
     source venv2/bin/activate && \
     python /usr/bin/nosetests tools && \
     deactivate"
