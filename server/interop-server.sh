#!/bin/bash
# Utility scripts.

SERVER=$(dirname ${BASH_SOURCE[0]})
REPO=${SERVER}/..

# Quit on any error.
set -e

# Run commands from context of server directory.
cd $SERVER

# Checks the health of everything.
if [ "$1" == "healthcheck" ]
then
    docker-compose run interop-server ./healthcheck.py --postgres_host interop-db --check_postgres --check_homepage
fi

# Creates the database. Only needs to be done once.
if [ "$1" == "create_db" ]
then
    docker-compose run interop-server ./healthcheck.py --postgres_host interop-db --check_postgres
    docker-compose run interop-server psql "postgresql://postgres:postgres@interop-db" -c "CREATE DATABASE auvsi_suas_db;"
    docker-compose run interop-server ./manage.py migrate
fi

# Drops the database. Dangerous!
if [ "$1" == "drop_db" ]
then
    docker-compose run interop-server ./healthcheck.py --postgres_host interop-db --check_postgres
    docker-compose run interop-server psql "postgresql://postgres:postgres@interop-db" -c "DROP DATABASE auvsi_suas_db;"
fi

# Loads test data. Optional, only needs to be done once.
if [ "$1" == "load_test_data" ]
then
    docker-compose run interop-server ./healthcheck.py --postgres_host interop-db --check_postgres
    docker-compose run interop-server ./config/load_test_data.py
fi

# Runs the interop system. Stops on Ctrl-C.
if [ "$1" == "up" ]
then
    docker-compose up
fi

# Runs the interop system detached. Stops on 'down'.
if [ "$1" == "up_d" ]
then
    docker-compose up -d
    docker-compose exec interop-server ./healthcheck.py --postgres_host interop-db --check_postgres --check_homepage
fi

# Stops the interop system previously started.
if [ "$1" == "down" ]
then
    docker-compose down
fi

# Gets a bash shell inside the server.
if [ "$1" == "shell" ]
then
    docker-compose exec interop-server bash
fi

# Upgrades the interop system.
if [ "$1" == "upgrade" ]
then
    docker-compose rm -v
    docker-compose pull
    docker-compose run interop-server ./manage.py migrate
fi

# Removes the container images and anonymous volumes.
if [ "$1" == "rm_data" ]
then
    docker-compose rm -v
    rm -rf volumes
fi

# Interop developer only. Teams need not run these.

# Pulls new images.
if [ "$1" == "pull" ]
then
    docker-compose pull
fi

# Builds container images.
if [ "$1" == "build" ]
then
    docker-compose build --pull
fi

# Migrates the database.
if [ "$1" == "migrate" ]
then
    docker-compose run interop-server ./manage.py migrate
fi

# Tests the system.
if [ "$1" == "test" ]
then
    docker-compose run interop-server ./manage.py test --parallel
fi
