#!/usr/bin/env python3
"""Installs test data into server."""

# Add server to Python path.
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Setup Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import logging
from auvsi_suas.models import test_utils
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def main():
    logger.info('Loading test data.')

    testadmin = get_user_model().objects.create_superuser(
        username='testadmin', password='testpass', email='test@test.com')
    testuser = get_user_model().objects.create_user(username='testuser',
                                                    password='testpass',
                                                    email='test@test.com')

    test_utils.create_sample_mission(testadmin)


if __name__ == "__main__":
    main()
