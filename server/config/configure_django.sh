#!/bin/bash
# Configures Django.

CONFIG=$(readlink -f $(dirname ${BASH_SOURCE[0]}))

set -e

sudo service postgresql start

cd ${CONFIG}/..
python manage.py collectstatic --noinput
python manage.py migrate
