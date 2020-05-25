"""Fly zone model."""

import datetime
import logging
import numpy as np
from auvsi_suas.models import aerial_position
from auvsi_suas.models.waypoint import Waypoint
from django.contrib import admin
from django.core import exceptions
from django.core import validators
from django.db import models
from matplotlib import path as mplpath

logger = logging.getLogger(__name__)

# The time window (in seconds) in which a plane cannot be counted as going out
# of bounds multiple times. This prevents noisy input data from recording
# significant more violations than a human observer.
OUT_OF_BOUNDS_DEBOUNCE_SEC = 10.0


class FlyZone(models.Model):
    """An approved area for UAS flight. UAS shall be in at least one zone."""

    # The polygon defining the boundary of the zone.
    boundary_pts = models.ManyToManyField(Waypoint)

    # The minimum altitude of the zone (MSL) in feet.
    altitude_msl_min = models.FloatField(
        validators=aerial_position.ALTITUDE_VALIDATORS)

    # The maximum altitude of the zone (MSL) in feet.
    altitude_msl_max = models.FloatField(
        validators=aerial_position.ALTITUDE_VALIDATORS)

    def clean(self):
        """Validates the model."""
        super(FlyZone, self).clean()
        if self.altitude_msl_min > self.altitude_msl_max:
            raise exceptions.ValidationError(
                'Altitude min must be less than altitude max.')

    def contains_pos(self, aerial_pos):
        """Whether the given pos is inside the zone.

        Args:
            aerial_pos: The AerialPosition to test.
        Returns:
            Whether the given position is inside the flight boundary.
        """
        return self.contains_many_pos([aerial_pos])[0]

    def contains_many_pos(self, aerial_pos_list):
        """Evaluates a list of positions more efficiently than inidividually.

        Args:
            aerial_pos_list: A list of AerialPositions to test.
        Returns:
            A list storing whether each position is inside the boundary.
        """
        # Get boundary points
        ordered_pts = self.boundary_pts.order_by('order')
        path_pts = [[wpt.latitude, wpt.longitude] for wpt in ordered_pts]
        # First check enough points to define a polygon
        if len(path_pts) < 3:
            return [False] * len(aerial_pos_list)

        # Create path to use for testing polygon inclusion
        path_pts.append(path_pts[0])
        path = mplpath.Path(np.array(path_pts))

        # Test each aerial position for altitude
        results = []
        for aerial_pos in aerial_pos_list:
            # Check altitude bounds
            alt = aerial_pos.altitude_msl
            altitude_check = (alt <= self.altitude_msl_max
                              and alt >= self.altitude_msl_min)
            results.append(altitude_check)

        # Create a list of positions to test whether inside polygon
        polygon_test_point_ids = [
            cur_id for cur_id in range(len(aerial_pos_list)) if results[cur_id]
        ]
        if len(polygon_test_point_ids) == 0:
            return results
        polygon_test_points = [[
            aerial_pos_list[cur_id].latitude, aerial_pos_list[cur_id].longitude
        ] for cur_id in polygon_test_point_ids]

        # Test each point for inside polygon
        polygon_test_results = path.contains_points(
            np.array(polygon_test_points))
        for test_id in range(len(polygon_test_point_ids)):
            cur_id = polygon_test_point_ids[test_id]
            results[cur_id] = polygon_test_results[test_id]

        return results

    @classmethod
    def out_of_bounds(cls, fly_zones, uas_telemetry_logs):
        """Determines amount of time spent out of bounds.

        Args:
            fly_zones: The list of FlyZone that the UAS must be in.
            uas_telemetry_logs: A list of UasTelemetry logs sorted by timestamp
                which demonstrate the flight of the UAS.
        Returns:
            num_violations: The number of times fly zone boundaries violated.
            total_time: The timedelta for time spent out of bounds
                as indicated by the telemetry logs.
        """
        # Get the aerial positions for the logs
        aerial_pos_list = uas_telemetry_logs
        log_ids_to_process = range(len(aerial_pos_list))

        # Evaluate zones against the logs, eliminating satisfied ones, until
        # only the out of boundary ids remain
        for zone in fly_zones:
            # Stop processing if no ids
            if len(log_ids_to_process) == 0:
                break
            # Evaluate the positions still not satisfied
            cur_positions = [
                aerial_pos_list[cur_id] for cur_id in log_ids_to_process
            ]
            satisfied_positions = zone.contains_many_pos(cur_positions)
            # Retain those which were not satisfied in this pass
            log_ids_to_process = [
                log_ids_to_process[cur_id]
                for cur_id in range(len(log_ids_to_process))
                if not satisfied_positions[cur_id]
            ]

        out_of_bounds_time = datetime.timedelta()
        violations = 0
        prev_event_id = -1
        currently_in_bounds = True
        out_of_bounds_ids = set(log_ids_to_process)
        for i in range(len(aerial_pos_list)):
            i_in_bounds = i not in out_of_bounds_ids
            if currently_in_bounds and not i_in_bounds:
                # As soon as there is one telemetry log out of bounds, we count
                # it as a violation.
                currently_in_bounds = False
                violations += 1
                prev_event_id = i
            elif not currently_in_bounds and i_in_bounds:
                # A switch of state needs to happen. But first make sure
                # enough time has passed.
                time_diff = (uas_telemetry_logs[i].timestamp -
                             uas_telemetry_logs[prev_event_id].timestamp)
                currently_in_bounds = (time_diff.total_seconds() >=
                                       OUT_OF_BOUNDS_DEBOUNCE_SEC)

            if not currently_in_bounds and i > 0:
                time_diff = (uas_telemetry_logs[i].timestamp -
                             uas_telemetry_logs[i - 1].timestamp)
                out_of_bounds_time += time_diff

        return (violations, out_of_bounds_time)


@admin.register(FlyZone)
class FlyZoneModelAdmin(admin.ModelAdmin):
    filter_horizontal = ("boundary_pts", )
    list_display = ('pk', 'altitude_msl_min', 'altitude_msl_max')
