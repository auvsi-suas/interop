"""Tests for the aerial_position module."""

from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from django.test import TestCase


class TestAerialPositionModel(TestCase):
    """Tests the AerialPosition model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        gps = GpsPosition(latitude=10, longitude=100)
        gps.save()

        pos = AerialPosition(gps_position=gps, altitude_msl=100)
        pos.save()

        pos.__unicode__()

    def assertDistanceEqual(self, pos1, pos2, dist, threshold=10):
        """AerialPosition distances are within threshold (ft)."""
        self.assertAlmostEqual(pos1.distance_to(pos2), dist, delta=threshold)
        self.assertAlmostEqual(pos2.distance_to(pos1), dist, delta=threshold)

    def evaluate_distance_inputs(self, io_list):
        """Evaluates the distance_to calc with the given input list."""
        for (lon1, lat1, alt1, lon2, lat2, alt2, dist_actual) in io_list:
            gps1 = GpsPosition(latitude=lat1, longitude=lon1)
            gps1.save()

            gps2 = GpsPosition(latitude=lat2, longitude=lon2)
            gps2.save()

            pos1 = AerialPosition(gps_position=gps1, altitude_msl=alt1)
            pos2 = AerialPosition(gps_position=gps2, altitude_msl=alt2)

            self.assertDistanceEqual(pos1, pos2, dist_actual)

    def test_distance_zero(self):
        """Tests distance calc for same position."""
        self.evaluate_distance_inputs([
            # (lon1, lat1, alt1, lon2, lat2, alt2, dist_actual)
            (0,      0,    0,    0,    0,    0,    0),
            (1,      2,    3,    1,    2,    3,    0),
            (-30,    30,   100,  -30,  30,   100,  0),
        ])  # yapf: disable

    def test_distance_competition_amounts(self):
        """Tests distance calc for competition amounts."""
        self.evaluate_distance_inputs([
            # (lon1,     lat1,      alt1, lon2,       lat2,      alt2, dist_actual)
            (-76.428709, 38.145306, 0,    -76.426375, 38.146146, 0,    736.4),
            (-76.428537, 38.145399, 0,    -76.427818, 38.144686, 100,  344.4),
            (-76.434261, 38.142471, 100,  -76.418876, 38.147838, 800,  4873.7),
        ])  # yapf: disable

    def test_duplicate_unequal(self):
        """Tests the duplicate function with unequal positions."""
        gps1 = GpsPosition(latitude=0, longitude=0)
        gps1.save()
        gps2 = GpsPosition(latitude=1, longitude=1)
        gps2.save()

        pos1 = AerialPosition(gps_position=gps1, altitude_msl=0)
        pos2 = AerialPosition(gps_position=gps2, altitude_msl=0)
        pos3 = AerialPosition(gps_position=gps1, altitude_msl=1)

        self.assertFalse(pos1.duplicate(pos2))
        self.assertFalse(pos1.duplicate(pos3))

    def test_duplicate_equal(self):
        """Tests the duplicate function with unequal positions."""
        gps1 = GpsPosition(latitude=0, longitude=0)
        gps1.save()
        gps2 = GpsPosition(latitude=0, longitude=0)
        gps2.save()

        pos1 = AerialPosition(gps_position=gps1, altitude_msl=0)
        pos2 = AerialPosition(gps_position=gps2, altitude_msl=0)
        pos3 = AerialPosition(gps_position=gps1, altitude_msl=0)

        self.assertTrue(pos1.duplicate(pos2))
        self.assertTrue(pos1.duplicate(pos3))
