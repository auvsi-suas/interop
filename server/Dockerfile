FROM ubuntu:14.04
WORKDIR /interop/server

# Install server base dependencies.
RUN sudo apt-get -qq update && sudo apt-get -qq install -y \
        apache2 \
        apache2-utils \
        curl \
        libapache2-mod-auth-pgsql \
        libapache2-mod-auth-plain \
        libapache2-mod-python \
        libapache2-mod-wsgi \
        libapache2-mod-xsendfile \
        memcached \
        nodejs \
        npm \
        postgresql \
        postgresql-client \
        protobuf-compiler \
        python \
        # Install from apt as it's much faster.
        python-matplotlib \
        python-numpy \
        python-pip \
        python-psycopg2 \
        python-pyproj \
        python-scipy

# Install server Javascript requirements.
RUN sudo ln -snf /usr/bin/nodejs /usr/local/bin/node && \
    sudo npm install -g \
        karma \
        karma-chrome-launcher \
        karma-jasmine \
        karma-phantomjs-launcher \
        phantomjs

# Install server Python requirements.
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Configure database, web server, Django.
COPY manage.py manage.py
COPY server server
COPY auvsi_suas/__init__.py auvsi_suas/__init__.py
COPY auvsi_suas/models/__init__.py auvsi_suas/models/__init__.py
COPY auvsi_suas/views/__init__.py auvsi_suas/views/__init__.py
COPY auvsi_suas/views/auvsi_admin/__init__.py auvsi_suas/views/auvsi_admin/__init__.py
COPY auvsi_suas/migrations auvsi_suas/migrations
COPY config config
COPY fixtures fixtures
RUN ./config/configure_postgresql.sh && \
    ./config/configure_apache.sh && \
    ./config/configure_django.sh

# Compile protobuf definitions.
COPY auvsi_suas/proto auvsi_suas/proto
RUN ./config/configure_proto.sh

# Copy remaining code.
COPY . .

# Load initial data.
RUN sudo service postgresql start && \
    python manage.py loaddata fixtures/test_fixture.yaml

# Host-mountable sections.
VOLUME /var/log/apache2 /var/lib/postgresql/9.3/data

# On run: start database, cache, server, and don't exit.
CMD sudo service postgresql start && \
  sudo service memcached start && \
  sudo service apache2 start && \
  tail -f /dev/null

HEALTHCHECK --interval=10s --timeout=3s \
    CMD curl -f http://localhost/ || exit 1
