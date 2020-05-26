"""Tests for the distance module."""

from auvsi_suas.models import distance
from django.test import TestCase


class TestHaversine(TestCase):
    """Tests the haversine code correctness."""
    def assertCloseEnough(self,
                          distance_actual,
                          distance_received,
                          threshold=0.003048):  # 10 feet in km
        """Determines whether the km distances given are close enough."""
        self.assertLessEqual(abs(distance_actual - distance_received),
                             threshold)

    def evaluate_inputs(self, input_output_list):
        """Evaluates a list of inputs and outputs."""
        for (lon1, lat1, lon2, lat2, distance_actual) in input_output_list:
            distance_received = distance.haversine(lon1, lat1, lon2, lat2)
            self.assertCloseEnough(distance_actual, distance_received)

    def test_zero_distance(self):
        """Tests various latitudes and longitudes which have zero distance."""
        self.evaluate_inputs([
            # (lon1, lat1, lon2, lat2, dist_actual)
            (0,      0,    0,    0,    0),
            (1,      1,    1,    1,    0),
            (-1,     -1,   -1,   -1,   0),
            (1,      -1,   1,    -1,   0),
            (-1,     1,    -1,   1,    0),
            (76,     42,   76,   42,   0),
            (-76,    42,   -76,  42,   0),
        ])  # yapf: disable

    def test_hemisphere_distances(self):
        """Tests distances in each hemisphere."""
        self.evaluate_inputs([
            # (lon1, lat1, lon2, lat2, dist_actual)
            (-73,    40,   -74,  41,   139.6886345468666),
            (73,     40,   74,   41,   139.6886345468667),
            (73,     -40,  74,   -41,  139.6886345468667),
            (-73,    -40,  -74,  -41,  139.68863454686704),
        ])  # yapf: disable

    def test_competition_distances(self):
        """Tests distances representative of competition amounts."""
        self.evaluate_inputs([
            # (lon1,     lat1,      lon2,       lat2,      dist_actual)
            (-76.428709, 38.145306, -76.426375, 38.146146, 0.22446),
            (-76.428537, 38.145399, -76.427818, 38.144686, 0.10045),
            (-76.434261, 38.142471, -76.418876, 38.147838, 1.46914),
        ])  # yapf: disable
