#!/usr/bin/env python
"""Checks health of server container.

Checks the following:
    1) Postgres is listening for connections.
    2) Apache is listening for connections.
    3) Homepage can be retrieved.
"""

import argparse
import requests
import retrying
import socket
import subprocess

MAX_DELAY = 5 * 60 * 1000  # 5 minutes.
WAIT = 1 * 1000  # 1 sec.


@retrying.retry(wait_fixed=WAIT, stop_max_delay=MAX_DELAY)
def check_postgres(host, port):
    """Check postgres health by querying pg_isready command line tool."""
    if subprocess.call(["pg_isready", "-q"]) == 1:
        raise Exception("PG not ready")


@retrying.retry(wait_fixed=WAIT, stop_max_delay=MAX_DELAY)
def check_apache(host, port):
    """Check apache health by attempting to create a TCP connection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.close()


@retrying.retry(wait_fixed=WAIT, stop_max_delay=MAX_DELAY)
def check_homepage(host, port):
    """Check homepage health by requesting via HTTP."""
    r = requests.get('http://%s:%d' % (host, port))
    assert r.status_code == 200


def main():
    parser = argparse.ArgumentParser(
        description='Checks health of server container.')

    parser.add_argument('--check_postgres', default=False, action='store_true')
    parser.add_argument('--postgres_host', type=str, default='localhost')
    parser.add_argument('--postgres_port', type=int, default=5432)

    parser.add_argument('--check_apache', default=False, action='store_true')
    parser.add_argument('--apache_host', type=str, default='localhost')
    parser.add_argument('--apache_port', type=int, default=80)

    parser.add_argument('--check_homepage', default=False, action='store_true')
    parser.add_argument('--homepage_host', type=str, default='localhost')
    parser.add_argument('--homepage_port', type=int, default=80)

    args = parser.parse_args()

    if args.check_postgres:
        check_postgres(args.postgres_host, args.postgres_port)
    if args.check_apache:
        check_apache(args.apache_host, args.apache_port)
    if args.check_homepage:
        check_homepage(args.homepage_host, args.homepage_port)


if __name__ == '__main__':
    main()
