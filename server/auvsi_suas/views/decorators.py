"""Simple decorators for views."""

import logging
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

logger = logging.getLogger(__name__)


def require_login(func):
    """Decorator to check that user is authenticated before allowing view.

    Raises:
        PermissionDenied: User is not authenticated.
    """
    def check_login(user):
        if not user.is_authenticated:
            raise PermissionDenied('Login required.')
        return True

    dec = user_passes_test(check_login)
    return dec(func)


def require_superuser(func):
    """Decorator to check that user is a superuser before allowing view.

    Raises:
        PermissionDenied: User is not a superuser.
    """
    def check_superuser(user):
        if not user.is_superuser:
            raise PermissionDenied('Only superusers allowed.')
        return True

    dec = user_passes_test(check_superuser)
    return dec(func)
