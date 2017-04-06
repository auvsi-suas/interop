import unittest

from . import FlyZone
from . import GpsPosition
from . import Mission
from . import MovingObstacle
from . import StationaryObstacle
from . import Target
from . import Telemetry
from . import Waypoint


class TestMission(unittest.TestCase):
    """Test the Mission object. There is very little to see here."""

    def test_serialize(self):
        """Test valid inputs serialize"""
        # No exceptions
        mission = Mission(
            id=1,
            active=True,
            air_drop_pos=GpsPosition(latitude=38,
                                     longitude=-76),
            fly_zones=[FlyZone(boundary_pts=[Waypoint(order=1,
                                                      latitude=37,
                                                      longitude=-70,
                                                      altitude_msl=10)],
                               altitude_msl_min=10,
                               altitude_msl_max=20)],
            home_pos=GpsPosition(latitude=39,
                                 longitude=-77),
            mission_waypoints=[Waypoint(order=1,
                                        latitude=37,
                                        longitude=-70,
                                        altitude_msl=10)],
            off_axis_target_pos=GpsPosition(latitude=37,
                                            longitude=-75),
            emergent_last_known_pos=GpsPosition(latitude=34,
                                                longitude=-75),
            search_grid_points=[Waypoint(order=1,
                                         latitude=37,
                                         longitude=-70,
                                         altitude_msl=10)])
        d = mission.serialize()
        self.assertEqual(1, d['id'])
        self.assertEqual(38, d['air_drop_pos']['latitude'])
        self.assertEqual(-77, d['home_pos']['longitude'])
        self.assertEqual(1, d['mission_waypoints'][0]['order'])
        self.assertEqual(37, d['off_axis_target_pos']['latitude'])
        self.assertEqual(34, d['emergent_last_known_pos']['latitude'])
        self.assertEqual(10, d['search_grid_points'][0]['altitude_msl'])

    def test_deserialize(self):
        """Test deserialization."""
        return
        m = Mission.deserialize({
            'id': 1,
            'active': True,
            'air_drop_pos': {
                'latitude': 38,
                'longitude': -76,
            },
            'fly_zones': [
                {
                    'altitude_msl_min': 10,
                    'altitude_msl_max': 20,
                    'boundary_pts': [
                        {
                            'order': 1,
                            'latitude': 37,
                            'longitude': -77,
                        },
                    ],
                },
            ],
            'home_pos': {
                'latitude': 39,
                'longitude': -75,
            },
            'mission_waypoints': [
                {
                    'order': 2,
                    'latitude': 30,
                    'longitude': -70,
                    'altitude_msl': 5,
                }
            ],
            'off_axis_target_pos': {
                'latitude': 31,
                'longitude': -71,
            },
            'emergent_last_known_pos': {
                'latitude': 32,
                'longitude': -71,
            },
            'search_grid_points': [
                {
                    'order': 3,
                    'latitude': 29,
                    'longitude': -72,
                },
            ],
        })

        self.assertEqual(1, m.id)
        self.assertTrue(m.active)
        self.assertEqual(38, m.air_drop_pos.latitude)
        self.assertEqual(-76, m.air_drop_pos.longitude)
        self.assertEqual(10, m.fly_zones[0].altitude_msl_min)
        self.assertEqual(20, m.fly_zones[0].altitude_msl_max)
        self.assertEqual(1, m.fly_zones[0].boundary_pts[0].order)
        self.assertEqual(37, m.fly_zones[0].boundary_pts[0].latitude)
        self.assertEqual(-77, m.fly_zones[0].boundary_pts[0].longitude)
        self.assertEqual(39, m.home_pos.latitude)
        self.assertEqual(-75, m.home_pos.latitude)
        self.assertEqual(2, m.mission_waypoints[0].order)
        self.assertEqual(30, m.mission_waypoints[0].latitude)
        self.assertEqual(-70, m.mission_waypoints[0].longitude)
        self.assertEqual(5, m.mission_waypoints[0].altitude_msl)
        self.assertEqual(31, m.off_axis_target_pos.latitude)
        self.assertEqual(-71, m.off_axis_target_pos.latitude)
        self.assertEqual(32, m.emergent_last_known_pos.latitude)
        self.assertEqual(-71, m.emergent_last_known_pos.latitude)
        self.assertEqual(3, m.search_grid_points[0].order)
        self.assertEqual(29, m.search_grid_points[0].latitude)
        self.assertEqual(-72, m.search_grid_points[0].longitude)


class TestTelemetry(unittest.TestCase):
    """Test the Telemetry object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        Telemetry(latitude=38, longitude=-76, altitude_msl=100, uas_heading=90)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            Telemetry(latitude='a',
                      longitude=-76,
                      altitude_msl=100,
                      uas_heading=90)
        # Bad longitude
        with self.assertRaises(ValueError):
            Telemetry(latitude=38,
                      longitude='a',
                      altitude_msl=100,
                      uas_heading=90)
        # Bad altitude
        with self.assertRaises(ValueError):
            Telemetry(latitude=38,
                      longitude=-76,
                      altitude_msl='a',
                      uas_heading=90)
        # Bad heading
        with self.assertRaises(ValueError):
            Telemetry(latitude=38,
                      longitude=-76,
                      altitude_msl=100,
                      uas_heading='a')

    def test_serialize(self):
        """Test serialization."""
        t = Telemetry(latitude=38,
                      longitude=-76,
                      altitude_msl=100,
                      uas_heading=90)
        s = t.serialize()

        self.assertEqual(4, len(s))
        self.assertEqual(38, s['latitude'])
        self.assertEqual(-76, s['longitude'])
        self.assertEqual(100, s['altitude_msl'])
        self.assertEqual(90, s['uas_heading'])

    def test_deserialize(self):
        """Test deserialization."""
        t = Telemetry.deserialize({
            'latitude': 38,
            'longitude': '-76',
            'altitude_msl': 100,
            'uas_heading': 90
        })

        self.assertEqual(38, t.latitude)
        self.assertEqual(-76, t.longitude)
        self.assertEqual(100, t.altitude_msl)
        self.assertEqual(90, t.uas_heading)


class TestStationaryObstacle(unittest.TestCase):
    """Test the StationaryObstacle object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        StationaryObstacle(latitude=38,
                           longitude=-76,
                           cylinder_radius=100,
                           cylinder_height=200)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude='a',
                               longitude=-76,
                               cylinder_radius=100,
                               cylinder_height=200)
        # Bad longitude
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38,
                               longitude='a',
                               cylinder_radius=100,
                               cylinder_height=200)
        # Bad radius
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38,
                               longitude=-76,
                               cylinder_radius='a',
                               cylinder_height=200)
        # Bad height
        with self.assertRaises(ValueError):
            StationaryObstacle(latitude=38,
                               longitude=-76,
                               cylinder_radius=100,
                               cylinder_height='a')

    def test_serialize(self):
        """Test serialization."""
        o = StationaryObstacle(latitude=38,
                               longitude=-76,
                               cylinder_radius=100,
                               cylinder_height=200)
        s = o.serialize()

        self.assertEqual(4, len(s))
        self.assertEqual(38, s['latitude'])
        self.assertEqual(-76, s['longitude'])
        self.assertEqual(100, s['cylinder_radius'])
        self.assertEqual(200, s['cylinder_height'])

    def test_deserialize(self):
        """Test deserialization."""
        o = StationaryObstacle.deserialize({
            'latitude': '38',
            'longitude': -76,
            'cylinder_radius': 100,
            'cylinder_height': 200
        })

        self.assertEqual(38, o.latitude)
        self.assertEqual(-76, o.longitude)
        self.assertEqual(100, o.cylinder_radius)
        self.assertEqual(200, o.cylinder_height)


class TestMovingObstacle(unittest.TestCase):
    """Test the MovingObstacle object. There is very little to see here."""

    def test_valid(self):
        """Test valid inputs"""
        # No exceptions
        MovingObstacle(latitude=38,
                       longitude=-76,
                       altitude_msl=100,
                       sphere_radius=200)

    def test_invalid(self):
        """Test invalid inputs"""
        # Bad latitude
        with self.assertRaises(ValueError):
            MovingObstacle(latitude='a',
                           longitude=-76,
                           altitude_msl=100,
                           sphere_radius=200)
        # Bad longitude
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38,
                           longitude='a',
                           altitude_msl=100,
                           sphere_radius=200)
        # Bad altitude
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38,
                           longitude=-76,
                           altitude_msl='a',
                           sphere_radius=-200)
        # Bad radius
        with self.assertRaises(ValueError):
            MovingObstacle(latitude=38,
                           longitude=-76,
                           altitude_msl=100,
                           sphere_radius='a')

    def test_serialize(self):
        """Test serialization."""
        o = MovingObstacle(latitude=38,
                           longitude=-76,
                           altitude_msl=100,
                           sphere_radius=200)
        s = o.serialize()

        self.assertEqual(4, len(s))
        self.assertEqual(38, s['latitude'])
        self.assertEqual(-76, s['longitude'])
        self.assertEqual(100, s['altitude_msl'])
        self.assertEqual(200, s['sphere_radius'])

    def test_deserialize(self):
        """Test deserialization."""
        o = MovingObstacle.deserialize({
            'latitude': 38,
            'longitude': -76,
            'altitude_msl': 100,
            'sphere_radius': 200
        })

        self.assertEqual(38, o.latitude)
        self.assertEqual(-76, o.longitude)
        self.assertEqual(100, o.altitude_msl)
        self.assertEqual(200, o.sphere_radius)


class TestTarget(unittest.TestCase):
    """Tests the Target model for validation and serialization."""

    def test_valid(self):
        """Test valid inputs."""
        Target(id=1,
               user=2,
               type='standard',
               latitude=10,
               longitude=-10,
               orientation='n',
               shape='circle',
               background_color='white',
               alphanumeric='a',
               alphanumeric_color='black')

        Target(type='off_axis',
               latitude=10,
               longitude=-10,
               orientation='n',
               shape='circle',
               background_color='white',
               alphanumeric='a',
               alphanumeric_color='black')

        Target(type='emergent',
               latitude=10,
               longitude=-10,
               description='Fireman putting out a fire.')

        Target(type='standard', latitude=10, longitude=-10, autonomous=True)

    def test_invalid(self):
        """Test invalid inputs."""
        # Bad latitude.
        with self.assertRaises(ValueError):
            Target(type='emergent',
                   latitude='a',
                   longitude=-10,
                   description='Firefighter')

        with self.assertRaises(ValueError):
            Target(type='emergent',
                   latitude=10,
                   longitude='a',
                   description='Firefighter')

    def test_serialize(self):
        """Test serialization."""
        o = Target(id=1,
                   user=2,
                   type='standard',
                   latitude=10,
                   longitude=-10,
                   orientation='n',
                   shape='circle',
                   background_color='white',
                   alphanumeric='a',
                   alphanumeric_color='black',
                   autonomous=True,
                   actionable_override=True,
                   team_id='testuser')
        s = o.serialize()

        self.assertEqual(13, len(s))
        self.assertEqual(1, s['id'])
        self.assertEqual(2, s['user'])
        self.assertEqual('standard', s['type'])
        self.assertEqual(10, s['latitude'])
        self.assertEqual(-10, s['longitude'])
        self.assertEqual('n', s['orientation'])
        self.assertEqual('circle', s['shape'])
        self.assertEqual('white', s['background_color'])
        self.assertEqual('a', s['alphanumeric'])
        self.assertEqual('black', s['alphanumeric_color'])
        self.assertEqual(True, s['autonomous'])
        self.assertEqual(True, s['actionable_override'])
        self.assertEqual('testuser', s['team_id'])

    def test_deserialize(self):
        """Test deserialization."""
        o = Target.deserialize({
            'type': 'standard',
            'latitude': '10',
            'longitude': -10,
            'orientation': 'n',
            'shape': 'circle',
            'background_color': 'white',
            'alphanumeric': 'a',
            'alphanumeric_color': 'black',
            'autonomous': True,
            'actionable_override': True,
            'team_id': 'testuser'
        })

        self.assertEqual('standard', o.type)
        self.assertEqual(10, o.latitude)
        self.assertEqual(-10, o.longitude)
        self.assertEqual('n', o.orientation)
        self.assertEqual('circle', o.shape)
        self.assertEqual('white', o.background_color)
        self.assertEqual('a', o.alphanumeric)
        self.assertEqual('black', o.alphanumeric_color)
        self.assertEqual(True, o.autonomous)
        self.assertEqual(True, o.actionable_override)
        self.assertEqual('testuser', o.team_id)

        o = Target.deserialize({'type': 'emergent'})

        self.assertEqual('emergent', o.type)
