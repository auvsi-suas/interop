"""Tests for the stationary_obstacle module."""

from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.uas_telemetry import UasTelemetry
from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase


class TestStationaryObstacleModel(TestCase):
    """Tests the StationaryObstacle model."""
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()

    def create_uas_logs(self, user, entries):
        """Create a list of uas telemetry logs.

        Args:
            user: User to create logs for.
            entries: List of (lat, lon, alt) tuples for each entry.

        Returns:
            List of UasTelemetry objects
        """
        ret = []

        for i in range(len(entries)):
            lat, lon, alt = entries[i]
            log = UasTelemetry()
            log.user = user
            log.latitude = lat
            log.longitude = lon
            log.altitude_msl = alt
            log.uas_heading = 0
            if i > 0:
                log.timetamp = ret[i - 1].timestamp + timedelta(seconds=1)
            log.save()
            ret.append(log)

        return ret

    def test_clean(self):
        """Tests model validation."""
        obst = StationaryObstacle(latitude=0,
                                  longitude=0,
                                  cylinder_radius=30,
                                  cylinder_height=10)
        obst.full_clean()

    def test_contains_pos(self):
        """Tests the inside obstacle method."""
        # (lat, lon, rad, height)
        TESTDATA_STATOBST_CONTAINSPOS_OBJ = (-76, 38, 100, 200)
        # (lat, lon, alt)
        TESTDATA_STATOBST_CONTAINSPOS_INSIDE = [
            (-76, 38, 0),
            (-76, 38, -1),
            (-76, 38, 200),
            (-76.0002, 38, 100),
            (-76, 38.0003, 100)
        ]  # yapf: disable
        TESTDATA_STATOBST_CONTAINSPOS_OUTSIDE = [
            (-76, 38, 201),
            (-76.0003, 38, 100),
            (-76, 38.004, 100)
        ]  # yapf: disable

        # Form the test obstacle
        obst = StationaryObstacle(
            latitude=TESTDATA_STATOBST_CONTAINSPOS_OBJ[0],
            longitude=TESTDATA_STATOBST_CONTAINSPOS_OBJ[1],
            cylinder_radius=TESTDATA_STATOBST_CONTAINSPOS_OBJ[2],
            cylinder_height=TESTDATA_STATOBST_CONTAINSPOS_OBJ[3])
        # Run test points against obstacle
        test_data = [(TESTDATA_STATOBST_CONTAINSPOS_INSIDE, True),
                     (TESTDATA_STATOBST_CONTAINSPOS_OUTSIDE, False)]
        for (cur_data, cur_contains) in test_data:
            for (lat, lon, alt) in cur_data:
                apos = AerialPosition(latitude=lat,
                                      longitude=lon,
                                      altitude_msl=alt)
                self.assertEqual(obst.contains_pos(apos), cur_contains)

    def test_evaluate_collision_with_uas(self):
        """Tests the collision with UAS method."""
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
             (-76, 38.002, 150),
             (-76, 38, 150),
             (-76, 38, 101)]
        )  # yapf: disable

        (cyl_details, inside_pos,
         outside_pos) = TESTDATA_STATOBST_EVALCOLLISION
        (cyl_lat, cyl_lon, cyl_height, cyl_rad) = cyl_details

        obst = StationaryObstacle(latitude=cyl_lat,
                                  longitude=cyl_lon,
                                  cylinder_radius=cyl_rad,
                                  cylinder_height=cyl_height)
        obst.save()

        inside_logs = []
        outside_logs = []
        logs_to_create = [(inside_pos, inside_logs),
                          (outside_pos, outside_logs)]

        for (positions, log_list) in logs_to_create:
            log_list += self.create_uas_logs(self.user, positions)

        # Assert collisions correctly evaluated
        collisions = [(inside_logs, True), (outside_logs, False)]
        for (log_list, inside) in collisions:
            self.assertEqual(obst.evaluate_collision_with_uas(log_list),
                             inside)
            for log in log_list:
                self.assertEqual(obst.evaluate_collision_with_uas([log]),
                                 inside)

        # Regression test past failed case.
        obst = StationaryObstacle(latitude=45.4342114,
                                  longitude=-71.8538153,
                                  cylinder_radius=10.0,
                                  cylinder_height=1300.0)
        logs = self.create_uas_logs(self.user, [
            (45.433839, -71.8523434, 770.013137988),
            (45.4338393, -71.8523446, 769.881926415),
        ])
        self.assertFalse(obst.evaluate_collision_with_uas(logs))
