"""Tests for the gps_position model."""

from auvsi_suas.models.gps_position import GpsPosition
from django.test import TestCase


class TestGpsPositionModel(TestCase):
    """Tests the GpsPosition model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        pos = GpsPosition(latitude=10, longitude=100)
        pos.save()

        pos.__unicode__()

    def assert_distance_equal(self, pos1, pos2, dist, threshold=10):
        """GpsPosition distances are within threshold (ft)."""
        self.assertAlmostEqual(pos1.distance_to(pos2), dist, delta=threshold)
        self.assertAlmostEqual(pos2.distance_to(pos1), dist, delta=threshold)

    def evaluate_distance_inputs(self, io_list):
        """Evaluates the distance_to calc with the given input list."""
        for (lon1, lat1, lon2, lat2, dist_actual) in io_list:
            gps1 = GpsPosition(latitude=lat1, longitude=lon1)
            gps1.save()

            gps2 = GpsPosition(latitude=lat2, longitude=lon2)
            gps2.save()

            self.assert_distance_equal(gps1, gps2, dist_actual)

    def test_distance_zero(self):
        """Tests distance calc for same position."""
        self.evaluate_distance_inputs([
            # (lon1, lat1, lon2, lat2, dist_actual)
            (0,      0,    0,    0,    0),
            (1,      1,    1,    1,    0),
            (-1,     -1,   -1,   -1,   0),
            (1,      -1,   1,    -1,   0),
            (-1,     1,    -1,   1,    0),
            (76,     42,   76,   42,   0),
            (-76,    42,   -76,  42,   0),
        ])  # yapf: disable

    def test_distance_competition_amounts(self):
        """Tests distance calc for competition amounts."""
        self.evaluate_distance_inputs([
            # (lon1,     lat1,      lon2,       lat2,      dist_actual)
            (-76.428709, 38.145306, -76.426375, 38.146146, 736.4),
            (-76.428537, 38.145399, -76.427818, 38.144686, 329.6),
            (-76.434261, 38.142471, -76.418876, 38.147838, 4820.0),
        ])  # yapf: disable

    def test_duplicate_unequal(self):
        """Tests the duplicate function for nonequal positions."""
        gps1 = GpsPosition(latitude=0, longitude=0)
        gps2 = GpsPosition(latitude=1, longitude=0)
        gps3 = GpsPosition(latitude=0, longitude=1)

        self.assertFalse(gps1.duplicate(gps2))
        self.assertFalse(gps1.duplicate(gps3))

    def test_duplicate_equal(self):
        """Tests the duplicate function for equal positiions."""
        gps1 = GpsPosition(latitude=1, longitude=1)
        gps2 = GpsPosition(latitude=1, longitude=1)

        self.assertTrue(gps1.duplicate(gps2))
