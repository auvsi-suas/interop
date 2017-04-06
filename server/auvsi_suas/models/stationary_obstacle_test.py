"""Tests for the stationary_obstacle module."""

from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.uas_telemetry import UasTelemetry
from django.contrib.auth.models import User
from django.test import TestCase

# (lat, lon, rad, height)
TESTDATA_STATOBST_CONTAINSPOS_OBJ = (-76, 38, 100, 200)
# (lat, lon, alt)
TESTDATA_STATOBST_CONTAINSPOS_INSIDE = [
    (-76, 38, 0),
    (-76, 38, 200),
    (-76.0002, 38, 100),
    (-76, 38.0003, 100)
]  # yapf: disable
TESTDATA_STATOBST_CONTAINSPOS_OUTSIDE = [
    (-76, 38, -1),
    (-76, 38, 201),
    (-76.0003, 38, 100),
    (-76, 38.004, 100)
]  # yapf: disable

TESTDATA_STATOBST_EVALCOLLISION = (
    # Cylinder position
    (-76, 38, 100, 100),
    # Inside positions
    [(-76, 38, 50),
     (-76, 38, 0),
     (-76, 38, 100),
     (-76.0001, 38.0001, 0),
     (-76.0001, 38.0001, 100)],
    # Outside positions
    [(-76.001, 38, 50),
     (-76, 38.002, 50),
     (-76, 38, -1),
     (-76, 38, 101)]
)  # yapf: disable


class TestStationaryObstacleModel(TestCase):
    """Tests the StationaryObstacle model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        pos = GpsPosition(latitude=100, longitude=200)
        pos.save()
        obst = StationaryObstacle(gps_position=pos,
                                  cylinder_radius=10,
                                  cylinder_height=100)
        obst.save()
        self.assertTrue(obst.__unicode__())

    def test_contains_pos(self):
        """Tests the inside obstacle method."""
        # Form the test obstacle
        pos = GpsPosition(latitude=TESTDATA_STATOBST_CONTAINSPOS_OBJ[0],
                          longitude=TESTDATA_STATOBST_CONTAINSPOS_OBJ[1])
        pos.save()
        obst = StationaryObstacle(
            gps_position=pos,
            cylinder_radius=TESTDATA_STATOBST_CONTAINSPOS_OBJ[2],
            cylinder_height=TESTDATA_STATOBST_CONTAINSPOS_OBJ[3])
        # Run test points against obstacle
        test_data = [
            (TESTDATA_STATOBST_CONTAINSPOS_INSIDE, True),
            (TESTDATA_STATOBST_CONTAINSPOS_OUTSIDE, False)
        ]
        for (cur_data, cur_contains) in test_data:
            for (lat, lon, alt) in cur_data:
                pos = GpsPosition(latitude=lat, longitude=lon)
                pos.save()
                apos = AerialPosition(gps_position=pos, altitude_msl=alt)
                self.assertEqual(obst.contains_pos(apos), cur_contains)

    def test_evaluate_collision_with_uas(self):
        """Tests the collision with UAS method."""
        # Create testing data
        user = User.objects.create_user('testuser', 'testemail@x.com',
                                        'testpass')
        user.save()

        (cyl_details, inside_pos,
         outside_pos) = TESTDATA_STATOBST_EVALCOLLISION
        (cyl_lat, cyl_lon, cyl_height, cyl_rad) = cyl_details

        gpos = GpsPosition(latitude=cyl_lat, longitude=cyl_lon)
        gpos.save()

        obst = StationaryObstacle(gps_position=gpos,
                                  cylinder_radius=cyl_rad,
                                  cylinder_height=cyl_height)
        obst.save()

        inside_logs = []
        outside_logs = []
        logs_to_create = [
            (inside_pos, inside_logs), (outside_pos, outside_logs)
        ]

        for (positions, log_list) in logs_to_create:
            for (lat, lon, alt) in positions:
                gpos = GpsPosition(latitude=lat, longitude=lon)
                gpos.save()
                apos = AerialPosition(gps_position=gpos, altitude_msl=alt)
                apos.save()
                log = UasTelemetry(user=user, uas_position=apos, uas_heading=0)
                log.save()
                log_list.append(log)
        # Assert collisions correctly evaluated
        collisions = [(inside_logs, True), (outside_logs, False)]
        for (log_list, inside) in collisions:
            self.assertEqual(
                obst.evaluate_collision_with_uas(log_list), inside)
            for log in log_list:
                self.assertEqual(
                    obst.evaluate_collision_with_uas([log]), inside)

    def test_json(self):
        """Tests the JSON serialization method."""
        TEST_LAT = 100.10
        TEST_LONG = 200.20
        TEST_RADIUS = 150.50
        TEST_HEIGHT = 75.30

        gpos = GpsPosition(latitude=TEST_LAT, longitude=TEST_LONG)
        gpos.save()
        obstacle = StationaryObstacle(gps_position=gpos,
                                      cylinder_radius=TEST_RADIUS,
                                      cylinder_height=TEST_HEIGHT)
        json_data = obstacle.json()

        self.assertTrue('latitude' in json_data)
        self.assertEqual(json_data['latitude'], TEST_LAT)
        self.assertTrue('longitude' in json_data)
        self.assertEqual(json_data['longitude'], TEST_LONG)
        self.assertTrue('cylinder_radius' in json_data)
        self.assertEqual(json_data['cylinder_radius'], TEST_RADIUS)
        self.assertTrue('cylinder_height' in json_data)
        self.assertEqual(json_data['cylinder_height'], TEST_HEIGHT)
