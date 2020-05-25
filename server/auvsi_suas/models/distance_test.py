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


class TestDistanceToLine(TestCase):
    """Tests distance_to_line."""

    # Use UTM 18N for all test cases.
    utm = distance.proj_utm(zone=18, north=True)

    def evaluate_inputs(self, inputs):
        """Evaluates a list of test cases."""
        for start, end, point, expected in inputs:
            dist = distance.distance_to_line(start, end, point, utm=self.utm)
            self.assertAlmostEqual(expected, dist, delta=5)  # ft

    def test_at_points(self):
        """Test inputs that are at or near the end points."""
        self.evaluate_inputs([
            # (start,        end,            point,          dist)
            ((38, -76, 100), (38, -77, 100), (38, -76, 100), 0),
            ((38, -76, 100), (38, -77, 100), (38, -77, 100), 0),
            ((38, -76, 100), (38, -77, 100), (38, -77, 0),   100),
            ((38, -76, 100), (38, -77, 100), (38, -77, 200), 100),
        ])  # yapf: disable

    def test_midpoint(self):
        """Test inputs that are along the middle of the line."""
        self.evaluate_inputs([
            (
                (38.145148, -76.427645, 100),  # start
                (38.145144, -76.426400, 100),  # end
                (38.145000, -76.427081, 100),  # point
                58,  # dist
            ),
            (
                (38.145148, -76.427645, 100),  # start
                (38.145144, -76.426400, 200),  # end
                (38.145000, -76.427081, 100),  # point
                70,  # dist
            ),
        ])  # yapf: disable

    def test_beyond_points(self):
        """Test inputs that are beyond the end of the line segment."""
        self.evaluate_inputs([
            (
                (38.145148, -76.427645, 100),  # start
                (38.145144, -76.426400, 100),  # end
                (38.145165, -76.427923, 100),  # point
                80,  # dist
            ),
            (
                (38.145148, -76.427645, 100),  # start
                (38.145144, -76.426400, 100),  # end
                (38.145591, -76.426127, 200),  # point
                207,  # dist
            ),
        ])  # yapf: disable
