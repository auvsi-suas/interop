"""GPS position model."""

import logging
from auvsi_suas.models import distance
from django.contrib import admin
from django.core import validators
from django.db import models

logger = logging.getLogger(__name__)


class GpsPositionMixin(models.Model):
    """GPS position mixin for adding a latitude and longitude degree value."""

    # Latitude in degrees.
    latitude = models.FloatField(validators=[
        validators.MinValueValidator(-90),
        validators.MaxValueValidator(90),
    ])
    # Longitude in degrees.
    longitude = models.FloatField(validators=[
        validators.MinValueValidator(-180),
        validators.MaxValueValidator(180),
    ])

    class Meta:
        abstract = True

    def distance_to(self, other):
        """Computes distance to another position.

        Args:
          other: The other position.
        Returns:
          Distance in feet.
        """
        return distance.distance_to(self.latitude, self.longitude, 0,
                                    other.latitude, other.longitude, 0)

    def duplicate(self, other):
        """Determines whether this GpsPosition is equivalent to another.

        This differs from the Django __eq__() method which simply compares
        primary keys. This method compares the field values.

        Args:
            other: The other position for comparison.
        Returns:
            True if they are equal.
        """
        return (self.latitude == other.latitude
                and self.longitude == other.longitude)


class GpsPosition(GpsPositionMixin):
    """GPS position object."""
    pass


@admin.register(GpsPosition)
class GpsPositionModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_display = ('pk', 'latitude', 'longitude')
