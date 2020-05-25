"""Aerial position model."""

import logging
from auvsi_suas.models import distance
from auvsi_suas.models.gps_position import GpsPositionMixin
from django.contrib import admin
from django.core import validators
from django.db import models

logger = logging.getLogger(__name__)

ALTITUDE_MSL_FT_MIN = -2000  # Lowest point on earth with buffer.
ALTITUDE_MSL_FT_MAX = 396000  # Edge of atmosphere.
ALTITUDE_VALIDATORS = [
    validators.MinValueValidator(ALTITUDE_MSL_FT_MIN),
    validators.MaxValueValidator(ALTITUDE_MSL_FT_MAX),
]


class AerialPositionMixin(GpsPositionMixin):
    """Aerial position mixin for adding a GPS position and altitude."""

    # Altitude (MSL) in feet.
    altitude_msl = models.FloatField(validators=ALTITUDE_VALIDATORS)

    class Meta:
        abstract = True

    def distance_to(self, other):
        """Computes distance to another position.

        Args:
          other: The other position.
        Returns:
          Distance in feet.
        """
        return distance.distance_to(self.latitude, self.longitude,
                                    self.altitude_msl, other.latitude,
                                    other.longitude, other.altitude_msl)

    def duplicate(self, other):
        """Determines whether this AerialPosition is equivalent to another.

        This differs from the Django __eq__() method which simply compares
        primary keys. This method compares the field values.

        Args:
            other: The other position for comparison.
        Returns:
            True if they are equal.
        """
        return (super(AerialPositionMixin, self).duplicate(other)
                and self.altitude_msl == other.altitude_msl)


class AerialPosition(AerialPositionMixin):
    """Aerial position object."""
    pass


@admin.register(AerialPosition)
class AerialPositionModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_display = ('pk', 'latitude', 'longitude', 'altitude_msl')
