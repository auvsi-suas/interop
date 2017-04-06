"""Tests for the missions module."""

import datetime
import functools
import json
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.views.missions import active_mission
from auvsi_suas.views.missions import mission_for_request
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.test import TestCase
from django.utils import timezone

login_url = reverse('auvsi_suas:login')
missions_url = reverse('auvsi_suas:missions')
missions_id_url = functools.partial(reverse, 'auvsi_suas:missions_id')


class TestMissionForRequest(TestCase):
    """Tests for function mission_for_request."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def create_config(self):
        """Creates a dummy config for testing."""
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 10
        pos.save()

        config = MissionConfig()
        config.is_active = False
        config.home_pos = pos
        config.emergent_last_known_pos = pos
        config.off_axis_target_pos = pos
        config.air_drop_pos = pos
        return config

    def test_noninteger_id(self):
        """Tests a non-integer mission ID in request."""
        params = {'mission': 'a'}
        _, err = mission_for_request(params)
        self.assertTrue(isinstance(err, HttpResponseBadRequest))

    def test_config_doesnt_exist(self):
        """Tests a mission ID for a mission that doesn't exist."""
        params = {'mission': '1'}
        _, err = mission_for_request(params)
        self.assertTrue(isinstance(err, HttpResponseBadRequest))

    def test_specified_mission(self):
        """Tests getting the mission for a specified ID."""
        config = self.create_config()
        config.is_active = False
        config.save()

        params = {'mission': str(config.pk)}
        recv_config, _ = mission_for_request(params)
        self.assertEqual(config, recv_config)

    def test_no_active_missions(self):
        """Tests when there are no active missions."""
        _, err = active_mission()
        self.assertTrue(isinstance(err, HttpResponseServerError))

        _, err = mission_for_request({})
        self.assertTrue(isinstance(err, HttpResponseServerError))

    def test_multiple_active_missions(self):
        """Tests when too many active missions."""
        config = self.create_config()
        config.is_active = True
        config.save()
        config = self.create_config()
        config.is_active = True
        config.save()

        _, err = active_mission()
        self.assertTrue(isinstance(err, HttpResponseServerError))

        _, err = mission_for_request({})
        self.assertTrue(isinstance(err, HttpResponseServerError))

    def test_active_mission(self):
        """Tests getting the single active mission."""
        config = self.create_config()
        config.is_active = True
        config.save()

        recv_config, _ = active_mission()
        self.assertEqual(config, recv_config)

        recv_config, _ = mission_for_request({})
        self.assertEqual(config, recv_config)


class TestMissionsViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.get(missions_url)
        self.assertEqual(403, response.status_code)

        response = self.client.get(missions_id_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestMissionsViewCommon(TestCase):
    """Common test setup"""

    def setUp(self):
        self.normaluser = User.objects.create_user(
            'normaluser', 'email@example.com', 'normalpass')
        self.normaluser.save()

        self.superuser = User.objects.create_superuser(
            'superuser', 'email@example.com', 'superpass')
        self.superuser.save()

    def Login(self, is_superuser):
        response = None
        if is_superuser:
            response = self.client.post(login_url, {
                'username': 'superuser',
                'password': 'superpass'
            })
        else:
            response = self.client.post(login_url, {
                'username': 'normaluser',
                'password': 'normalpass'
            })
        self.assertEqual(200, response.status_code)


class TestMissionsViewBasic(TestMissionsViewCommon):
    """Tests the missions view with minimal data."""

    def test_post(self):
        """POST not allowed"""
        self.Login(is_superuser=False)
        response = self.client.post(missions_url)
        self.assertEqual(405, response.status_code)

    def test_no_missions(self):
        """No missions results in empty list."""
        self.Login(is_superuser=False)
        response = self.client.get(missions_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.content))

    def test_incorrect_mission(self):
        self.Login(is_superuser=False)
        response = self.client.get(missions_id_url(args=[1]))
        self.assertEqual(404, response.status_code)


class TestMissionsViewSampleMission(TestMissionsViewCommon):
    """Tests the missions view with sample mission."""

    fixtures = ['testdata/sample_mission.json']

    def assert_non_superuser_data(self, data):
        self.assertIn('id', data)
        self.assertEqual(3, data['id'])

        self.assertIn('active', data)
        self.assertEqual(True, data['active'])

        self.assertIn('home_pos', data)
        self.assertIn('latitude', data['home_pos'])
        self.assertIn('longitude', data['home_pos'])
        self.assertEqual(38.0, data['home_pos']['latitude'])
        self.assertEqual(-79.0, data['home_pos']['longitude'])

        self.assertIn('mission_waypoints', data)
        for waypoint in data['mission_waypoints']:
            self.assertIn('order', waypoint)
            self.assertIn('latitude', waypoint)
            self.assertIn('longitude', waypoint)
            self.assertIn('altitude_msl', waypoint)

        self.assertEqual(2, len(data['mission_waypoints']))

        self.assertEqual(0, data['mission_waypoints'][0]['order'])
        self.assertEqual(38.0, data['mission_waypoints'][0]['latitude'])
        self.assertEqual(-76.0, data['mission_waypoints'][0]['longitude'])
        self.assertEqual(30.0, data['mission_waypoints'][0]['altitude_msl'])

        self.assertEqual(1, data['mission_waypoints'][1]['order'])
        self.assertEqual(38.0, data['mission_waypoints'][1]['latitude'])
        self.assertEqual(-77.0, data['mission_waypoints'][1]['longitude'])
        self.assertEqual(60.0, data['mission_waypoints'][1]['altitude_msl'])

        self.assertIn('search_grid_points', data)
        for point in data['search_grid_points']:
            self.assertIn('order', point)
            self.assertIn('latitude', point)
            self.assertIn('longitude', point)
            self.assertIn('altitude_msl', point)

        self.assertEqual(1, len(data['search_grid_points']))

        self.assertEqual(10, data['search_grid_points'][0]['order'])
        self.assertEqual(38.0, data['search_grid_points'][0]['latitude'])
        self.assertEqual(-79.0, data['search_grid_points'][0]['longitude'])
        self.assertEqual(1000.0, data['search_grid_points'][0]['altitude_msl'])

        self.assertIn('off_axis_target_pos', data)
        self.assertIn('latitude', data['off_axis_target_pos'])
        self.assertIn('longitude', data['off_axis_target_pos'])
        self.assertEqual(38.0, data['off_axis_target_pos']['latitude'])
        self.assertEqual(-79.0, data['off_axis_target_pos']['longitude'])

        self.assertIn('emergent_last_known_pos', data)
        self.assertIn('latitude', data['emergent_last_known_pos'])
        self.assertIn('longitude', data['emergent_last_known_pos'])
        self.assertEqual(38.0, data['emergent_last_known_pos']['latitude'])
        self.assertEqual(-79.0, data['emergent_last_known_pos']['longitude'])

        self.assertIn('air_drop_pos', data)
        self.assertIn('latitude', data['air_drop_pos'])
        self.assertIn('longitude', data['air_drop_pos'])
        self.assertEqual(38.0, data['air_drop_pos']['latitude'])
        self.assertEqual(-79.0, data['air_drop_pos']['longitude'])

    def assert_non_superuser_data_array(self, data):
        self.assertEqual(1, len(data))
        self.assert_non_superuser_data(data[0])

    def test_non_superuser(self):
        """Response JSON is properly formatted for non-superuser."""
        self.Login(is_superuser=False)
        response = self.client.get(missions_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)

        self.assert_non_superuser_data_array(data)
        self.assertNotIn('stationary_obstacles', data[0])
        self.assertNotIn('moving_obstacles', data[0])

        response = self.client.get(missions_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(data, json.loads(response.content))

    def test_superuser(self):
        """Response JSON is properly formatted for superuser."""
        self.Login(is_superuser=True)
        response = self.client.get(missions_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)

        self.assert_non_superuser_data_array(data)
        self.assertIn('stationary_obstacles', data[0])
        self.assertIn('moving_obstacles', data[0])

        response = self.client.get(missions_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(data, json.loads(response.content))

    def test_non_superuser_id(self):
        """Mission ID response JSON is properly formatted for non-superuser."""
        self.Login(is_superuser=False)
        response = self.client.get(missions_id_url(args=[3]))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)

        self.assert_non_superuser_data(data)
        self.assertNotIn('stationary_obstacles', data)
        self.assertNotIn('moving_obstacles', data)

    def test_superuser_id(self):
        """Mission ID response JSON is properly formatted for superuser."""
        self.Login(is_superuser=True)
        response = self.client.get(missions_id_url(args=[3]))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)

        self.assert_non_superuser_data(data)
        self.assertIn('stationary_obstacles', data)
        self.assertIn('moving_obstacles', data)
