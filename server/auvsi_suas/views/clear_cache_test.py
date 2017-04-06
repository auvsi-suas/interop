"""Tests the clear cache view."""

import datetime
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase


class TestClearCache(TestCase):
    """Tests clearing the cache view."""

    def setUp(self):
        """Populates an active mission to test a cached view."""
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 10
        pos.save()
        self.pos = pos

        obst = StationaryObstacle()
        obst.gps_position = pos
        obst.cylinder_radius = 10
        obst.cylinder_height = 10
        obst.save()
        self.obst = obst

        config = MissionConfig()
        config.is_active = True
        config.home_pos = pos
        config.emergent_last_known_pos = pos
        config.off_axis_target_pos = pos
        config.air_drop_pos = pos
        config.save()
        self.config = config
        config.stationary_obstacles.add(obst)
        config.save()

        self.login_url = reverse('auvsi_suas:login')
        self.obst_url = reverse('auvsi_suas:obstacles')
        self.clear_cache_url = reverse('auvsi_suas:clear_cache')

    def test_clear_nonadmin(self):
        """Tests the clear cache responds with error for nonadmin."""
        # Create non-admin user and login.
        user = User.objects.create_user('testuser', 'email@example.com',
                                        'testpass')
        user.save()
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)
        # Check an error is returned.
        response = self.client.get(self.clear_cache_url)
        self.assertGreaterEqual(response.status_code, 300)

    def test_clear(self):
        """Tests the clear cache view."""
        # Create admin user and login
        superuser = User.objects.create_superuser(
            'superuser', 'email@example.com', 'superpass')
        superuser.save()
        response = self.client.post(self.login_url, {
            'username': 'superuser',
            'password': 'superpass'
        })
        self.assertEqual(200, response.status_code)
        # Execute a cached view.
        response = self.client.get(self.obst_url)
        self.assertEqual(response.status_code, 200)
        # Change the underlying value.
        self.pos.latitude = 100
        self.pos.save()
        # Get the cached value.
        cached_response = self.client.get(self.obst_url)
        self.assertEqual(cached_response.status_code, 200)
        self.assertEqual(response.content, cached_response.content)
        # Clear the cache and test view now shows updated value.
        response = self.client.get(self.clear_cache_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.obst_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, cached_response.content)
