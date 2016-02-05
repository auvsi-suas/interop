import unittest

from . import Telemetry, StationaryObstacle, MovingObstacle, Target


class TestTelemetry(unittest.TestCase):
    """Test the Telemetry object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        Telemetry(latitude=38.0,
                  longitude=-76.0,
                  altitude_msl=100.0,
                  uas_heading=90.0)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            Telemetry(latitude=120.0,
                      longitude=-76.0,
                      altitude_msl=100.0,
                      uas_heading=90.0)

        # Bad longitude
        with self.assertRaises(ValueError):
            Telemetry(latitude=38.0,
                      longitude=-200.0,
                      altitude_msl=100.0,
                      uas_heading=90.0)

        # Bad heading
        with self.assertRaises(ValueError):
            Telemetry(latitude=38.0,
                      longitude=-76.0,
                      altitude_msl=100.0,
                      uas_heading=-90.0)

        # Bad type
        with self.assertRaises(ValueError):
            Telemetry(latitude=38,
                      longitude="Webster Field",
                      altitude_msl=100,
                      uas_heading=90)


class TestStationaryObstacle(unittest.TestCase):
    """Test the StationaryObstacle object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        StationaryObstacle(latitude=38.0,
                           longitude=-76.0,
                           cylinder_radius=100.0,
                           cylinder_height=200.0)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=120.0,
                               longitude=-76.0,
                               cylinder_radius=100.0,
                               cylinder_height=200.0)

        # Bad longitude
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38.0,
                               longitude=-200.0,
                               cylinder_radius=100.0,
                               cylinder_height=200.0)

        # Bad radius
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38.0,
                               longitude=-76.0,
                               cylinder_radius=-100.0,
                               cylinder_height=200.0)

        # Bad height
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38.0,
                               longitude=-76.0,
                               cylinder_radius=100.0,
                               cylinder_height=-200.0)

        # Bad type
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38.0,
                               longitude="Webster Field",
                               cylinder_radius=100.0,
                               cylinder_height=90.0)


class TestMovingObstacle(unittest.TestCase):
    """Test the MovingObstacle object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        MovingObstacle(latitude=38.0,
                       longitude=-76.0,
                       altitude_msl=100.0,
                       sphere_radius=200.0)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=120.0,
                           longitude=-76.0,
                           altitude_msl=100.0,
                           sphere_radius=200.0)

        # Bad longitude
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38.0,
                           longitude=-200.0,
                           altitude_msl=100.0,
                           sphere_radius=200.0)

        # Bad radius
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38.0,
                           longitude=-76.0,
                           altitude_msl=100.0,
                           sphere_radius=-200.0)

        # Bad type
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38.0,
                           longitude="Webster Field",
                           altitude_msl=100.0,
                           sphere_radius=90.0)


class TestTarget(unittest.TestCase):
    """Tests the Target model for validation and serialization."""

    def test_valid(self):
        """Test valid inputs."""
        Target(type='standard',
               latitude=10.0,
               longitude=-10.0,
               orientation='n',
               shape='circle',
               background_color='white',
               alphanumeric='a',
               alphanumeric_color='black')

        Target(type='qrc',
               latitude=10.0,
               longitude=-10.0,
               description='http://test.com')

        Target(type='off_axis',
               latitude=10.0,
               longitude=-10.0,
               orientation='n',
               shape='circle',
               background_color='white',
               alphanumeric='a',
               alphanumeric_color='black')

        Target(type='emergent',
               latitude=10.0,
               longitude=-10.0,
               description='Fireman putting out a fire.')

    def test_invalid(self):
        """Test invalid inputs."""
        with self.assertRaises(ValueError):
            Target(type=None, latitude=10.0, longitude=10.0)

        with self.assertRaises(ValueError):
            Target(type='qrc',
                   latitude=10000.0,
                   longitude=-10.0,
                   description='http://test.com')

        with self.assertRaises(ValueError):
            Target(type='qrc',
                   latitude=10.0,
                   longitude=-10000.0,
                   description='http://test.com')

        with self.assertRaises(ValueError):
            Target(type='standard',
                   latitude=10.0,
                   longitude=-10.0,
                   orientation='n',
                   shape='circle',
                   background_color='white',
                   alphanumeric='abc',
                   alphanumeric_color='black')

        with self.assertRaises(ValueError):
            Target(type='standard',
                   latitude=10.0,
                   longitude=-10.0,
                   orientation='n',
                   shape='circle',
                   background_color='white',
                   alphanumeric='.',
                   alphanumeric_color='black')
