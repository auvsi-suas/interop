"""Tests for the obstacles module."""

import datetime
import json
import logging
import time
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.waypoint import Waypoint
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils import timezone

login_url = reverse('auvsi_suas:login')
obstacle_url = reverse('auvsi_suas:obstacles')


class TestObstaclesViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.get(obstacle_url)
        self.assertEqual(403, response.status_code)


class TestObstaclesViewCommon(TestCase):
    """Obstacles view common test setup."""

    def create_stationary_obstacle(self, lat, lon, radius, height):
        """Create a new StationaryObstacle model.

        Args:
            lat: Latitude of centroid
            lon: Longitude of centroid
            radius: Cylinder radius
            height: Cylinder height

        Returns:
            Saved StationaryObstacle
        """
        gps = GpsPosition(latitude=lat, longitude=lon)
        gps.save()

        obstacle = StationaryObstacle(gps_position=gps,
                                      cylinder_radius=radius,
                                      cylinder_height=height)
        obstacle.save()
        return obstacle

    def create_moving_obstacle(self, waypoints):
        """Create a new MovingObstacle model.

        Args:
            waypoints: List of (lat, lon, alt) tuples

        Returns:
            Saved MovingObstacle
        """
        obstacle = MovingObstacle(speed_avg=40, sphere_radius=100)
        obstacle.save()

        for num, waypoint in enumerate(waypoints):
            (lat, lon, alt) = waypoint

            gps = GpsPosition(latitude=lat, longitude=lon)
            gps.save()

            pos = AerialPosition(gps_position=gps, altitude_msl=alt)
            pos.save()

            waypoint = Waypoint(order=num, position=pos)
            waypoint.save()

            obstacle.waypoints.add(waypoint)

        obstacle.save()
        return obstacle

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'email@example.com',
                                             'testpass')
        self.user.save()

        # Create an active mission.
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 10
        pos.save()
        config = MissionConfig()
        config.is_active = True
        config.home_pos = pos
        config.emergent_last_known_pos = pos
        config.off_axis_target_pos = pos
        config.air_drop_pos = pos
        config.save()

        # Add a couple of stationary obstacles
        obst = self.create_stationary_obstacle(lat=38.142233,
                                               lon=-76.434082,
                                               radius=300,
                                               height=500)
        config.stationary_obstacles.add(obst)

        obst = self.create_stationary_obstacle(lat=38.442233,
                                               lon=-76.834082,
                                               radius=100,
                                               height=750)
        config.stationary_obstacles.add(obst)

        # And a couple of moving obstacles
        obst = self.create_moving_obstacle([
            # (lat,     lon,        alt)
            (38.142233, -76.434082, 300),
            (38.141878, -76.425198, 700),
        ])
        config.moving_obstacles.add(obst)

        obst = self.create_moving_obstacle([
            # (lat,     lon,        alt)
            (38.145405, -76.428310, 100),
            (38.146582, -76.424099, 200),
            (38.144662, -76.427634, 300),
            (38.147729, -76.419185, 200),
            (38.147573, -76.420832, 100),
            (38.148522, -76.419507, 750),
        ])
        config.moving_obstacles.add(obst)

        config.save()

        # Login
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)


class TestObstaclesView(TestObstaclesViewCommon):
    """Tests the obstacles view."""

    def test_post(self):
        """POST requests are not allowed."""
        response = self.client.post(obstacle_url)
        self.assertEqual(405, response.status_code)

    def test_correct_json(self):
        """Tests that access is logged and returns valid response."""
        response = self.client.get(obstacle_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertIn('stationary_obstacles', data)
        self.assertEqual(2, len(data['stationary_obstacles']))
        for obstacle in data['stationary_obstacles']:
            self.assertIn('latitude', obstacle)
            self.assertIn('longitude', obstacle)
            self.assertIn('cylinder_radius', obstacle)
            self.assertIn('cylinder_height', obstacle)

        self.assertIn('moving_obstacles', data)
        self.assertEqual(2, len(data['moving_obstacles']))
        for obstacle in data['moving_obstacles']:
            self.assertIn('latitude', obstacle)
            self.assertIn('longitude', obstacle)
            self.assertIn('altitude_msl', obstacle)
            self.assertIn('sphere_radius', obstacle)

    def test_different(self):
        """Responses at different times are different (moving obstacles move)"""
        response = self.client.get(obstacle_url)
        self.assertEqual(200, response.status_code)

        data1 = json.loads(response.content)

        response = self.client.get(obstacle_url)
        self.assertEqual(200, response.status_code)

        data2 = json.loads(response.content)

        self.assertNotEqual(data1, data2)

    def test_no_time(self):
        """Normal users cannot set time."""
        response = self.client.get(obstacle_url, {
            'time': timezone.now().isoformat(),
        })
        self.assertEqual(400, response.status_code)

    def test_loadtest(self):
        """Tests the max load the view can handle."""
        if not settings.TEST_ENABLE_LOADTEST:
            return

        total_ops = 0
        start_t = time.clock()
        while time.clock() - start_t < settings.TEST_LOADTEST_TIME:
            self.client.get(obstacle_url)
            total_ops += 1
        end_t = time.clock()
        total_t = end_t - start_t
        op_rate = total_ops / total_t

        print 'Obstacle Info Rate (%f)' % op_rate
        self.assertGreaterEqual(op_rate,
                                settings.TEST_LOADTEST_INTEROP_MIN_RATE)


class TestObstaclesViewSuperuser(TestObstaclesViewCommon):
    """Tests the obstacles view as superuser."""

    def setUp(self):
        super(TestObstaclesViewSuperuser, self).setUp()

        self.user = User.objects.create_superuser(
            'superuser', 'email@example.com', 'superpass')
        self.user.save()

        # Login
        response = self.client.post(login_url, {
            'username': 'superuser',
            'password': 'superpass'
        })
        self.assertEqual(200, response.status_code)

    def test_bad_time(self):
        """Bad time format rejected."""
        response = self.client.get(obstacle_url, {
            'time': 'June 1, 2000',
        })  # yapf: disable
        self.assertEqual(400, response.status_code)

    def test_same_time(self):
        """Obstacles at the same time are the same."""
        time = timezone.now().isoformat()

        response = self.client.get(obstacle_url, {
            'time': time,
        })  # yapf: disable
        self.assertEqual(200, response.status_code)

        data1 = json.loads(response.content)

        response = self.client.get(obstacle_url, {
            'time': time,
        })  # yapf: disable
        self.assertEqual(200, response.status_code)

        data2 = json.loads(response.content)

        self.assertEqual(data1, data2)
