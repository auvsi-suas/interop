FROM ubuntu:20.04
WORKDIR /interop/server

# Set the time zone to the competition time zone.
RUN ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime

# Install server base dependencies.
RUN apt-get -qq update && apt-get -qq install -y \
        nginx \
        npm \
        postgresql-client \
        protobuf-compiler \
        python3 \
        # Install from apt as it's much faster.
        python3-matplotlib \
        python3-numpy \
        python3-pip \
        python3-psycopg2 \
        python3-pyproj \
        sudo

# Create storage for object images.
RUN mkdir -p /var/www/media/objects && \
    chown -R www-data /var/www

# Install server Python requirements.
COPY server/config/requirements.txt config/requirements.txt
RUN pip3 install -r config/requirements.txt

# Install server JS requirements.
COPY server/config/npm.txt config/npm.txt
RUN cat config/npm.txt | xargs sudo npm install -g

# Configure web server.
COPY server/config/nginx.conf /etc/nginx/sites-enabled/default
RUN sudo mkdir -p /var/log/uwsgi

# Compile static assets.
COPY server/manage.py manage.py
COPY server/server server
COPY server/auvsi_suas/__init__.py auvsi_suas/__init__.py
COPY server/auvsi_suas/models/__init__.py auvsi_suas/models/__init__.py
COPY server/auvsi_suas/views/__init__.py auvsi_suas/views/__init__.py
COPY server/auvsi_suas/frontend auvsi_suas/frontend
RUN ./manage.py collectstatic --noinput

# Copy all remaining code.
COPY server/ .

# Compile protobuf definitions.
COPY proto auvsi_suas/proto
RUN protoc --python_out=. auvsi_suas/proto/*.proto

# Host-mountable sections.
VOLUME /var/log/uwsgi /var/lib/postgresql /var/www/media/objects

# Commands to execute on startup.
CMD uwsgi --ini config/uwsgi.ini && \
    sudo nginx && \
    tail -f /dev/null

# Command to check health of container.
HEALTHCHECK \
  CMD ./healthcheck.py --check_homepage
