"""Tests for the waypoint module."""

from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.waypoint import Waypoint
from django.test import TestCase


class TestWaypointModel(TestCase):
    """Tests the Waypoint model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        gps = GpsPosition(latitude=10, longitude=100)
        gps.save()

        pos = AerialPosition(gps_position=gps, altitude_msl=100)
        pos.save()

        wpt = Waypoint(position=pos, order=10)
        wpt.save()

        wpt.__unicode__()

    def assertDistanceEqual(self, wpt1, wpt2, dist, threshold=10):
        """Waypoint distances are within threshold (ft)."""
        self.assertAlmostEqual(wpt1.distance_to(wpt2), dist, delta=threshold)
        self.assertAlmostEqual(wpt2.distance_to(wpt1), dist, delta=threshold)

    def evaluate_inputs(self, io_list):
        for (lon1, lat1, alt1, lon2, lat2, alt2, dist) in io_list:
            gps1 = GpsPosition(latitude=lat1, longitude=lon1)
            gps1.save()

            gps2 = GpsPosition(latitude=lat2, longitude=lon2)
            gps2.save()

            pos1 = AerialPosition(gps_position=gps1, altitude_msl=alt1)
            pos1.save()

            pos2 = AerialPosition(gps_position=gps2, altitude_msl=alt2)
            pos2.save()

            wpt1 = Waypoint(position=pos1)
            wpt2 = Waypoint(position=pos2)

            self.assertDistanceEqual(wpt1, wpt2, dist)

    def test_distance(self):
        """Tests the distance calculation executes correctly."""
        self.evaluate_inputs([
            # (lon1,     lat1,      alt1, lon2,       lat2,      alt2, dist_actual)
            (-76.428709, 38.145306, 0,    -76.426375, 38.146146, 0,    736.4),
            (-76.428537, 38.145399, 0,    -76.427818, 38.144686, 100,  344.4),
            (-76.434261, 38.142471, 100,  -76.418876, 38.147838, 800,  4873.7),
        ])  # yapf: disable
