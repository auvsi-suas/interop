FROM ubuntu:14.04
WORKDIR /interop/client

RUN sudo apt-get -qq update && sudo apt-get -qq install -y \
        python \
        python-dev \
        python-nose \
        python-pip \
        python-pyproj \
        python-virtualenv \
        python-lxml \
        python3 \
        python3-dev \
        python3-nose \
        python3-pip \
        python3-pyproj \
        python3-lxml

COPY requirements.txt requirements.txt
RUN bash -c "virtualenv --system-site-packages -p /usr/bin/python2 \
            /interop/client/venv2 && \
        source /interop/client/venv2/bin/activate && \
        pip install -r requirements.txt && \
        deactivate" && \
    bash -c "virtualenv --system-site-packages -p /usr/bin/python3 \
            /interop/client/venv3 && \
        source /interop/client/venv3/bin/activate && \
        pip3 install -r requirements.txt && \
        deactivate"

COPY . .

CMD bash --init-file configure.sh
