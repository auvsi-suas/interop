"""Admin view to clear the cache."""

import logging
from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_superuser
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View


class ClearCache(View):
    """Clears the cache on admin's request."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(ClearCache, self).dispatch(*args, **kwargs)

    def get(self, request):
        logger.info('Admin requested to clear the cache.')
        cache.clear()
        return HttpResponse("Cache cleared.")


@receiver(post_save, sender=FlyZone)
@receiver(post_save, sender=MissionConfig)
@receiver(post_save, sender=MovingObstacle)
@receiver(post_save, sender=StationaryObstacle)
@receiver(post_save, sender=Waypoint)
def clear_cache_on_invalidation(sender, **kwargs):
    """Clears the cache when certain models are updated."""
    logging.info('Model saved invalidating caches, clearing them. Model: %s.',
                 sender)
    cache.clear()
