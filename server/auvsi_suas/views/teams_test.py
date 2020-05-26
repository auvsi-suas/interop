"""Tests for the teams module."""

import dateutil.parser
import functools
import json
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.models.waypoint import Waypoint
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

teams_url = reverse('auvsi_suas:teams')
team_url = functools.partial(reverse, 'auvsi_suas:team')


class TestTeamsViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.get(teams_url)
        self.assertEqual(403, response.status_code)


class TestTeamsView(TestCase):
    """Tests the teams view."""
    def setUp(self):
        self.superuser = User.objects.create_superuser('superuser',
                                                       'email@example.com',
                                                       'superpass')
        self.superuser.save()
        self.client.force_login(self.superuser)

    def create_data(self):
        """Create a basic sample dataset."""
        self.user1 = User.objects.create_user('user1', 'email@example.com',
                                              'testpass')
        self.user1.save()

        self.user2 = User.objects.create_user('user2', 'email@example.com',
                                              'testpass')
        self.user2.save()

        # Mission
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        wpt = Waypoint()
        wpt.order = 10
        wpt.latitude = 10
        wpt.longitude = 100
        wpt.altitude_msl = 1000
        wpt.save()
        self.mission = MissionConfig()
        self.mission.home_pos = pos
        self.mission.lost_comms_pos = pos
        self.mission.emergent_last_known_pos = pos
        self.mission.off_axis_odlc_pos = pos
        self.mission.map_center_pos = pos
        self.mission.map_height_ft = 1
        self.mission.air_drop_pos = pos
        self.mission.ugv_drive_pos = pos
        self.mission.save()
        self.mission.mission_waypoints.add(wpt)
        self.mission.search_grid_points.add(wpt)
        self.mission.save()

        # user1 is flying
        event = TakeoffOrLandingEvent(user=self.user1,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()

        # user2 has landed
        event = TakeoffOrLandingEvent(user=self.user2,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()
        event = TakeoffOrLandingEvent(user=self.user2,
                                      mission=self.mission,
                                      uas_in_air=False)
        event.save()

        # user2 is active
        self.timestamp = timezone.now()

        self.telem = UasTelemetry(user=self.user2,
                                  latitude=38.6462,
                                  longitude=-76.2452,
                                  altitude_msl=0,
                                  uas_heading=90)
        self.telem.save()
        self.telem.timestamp = dateutil.parser.parse(
            u'2016-10-01T00:00:00.0+00:00')

        self.telem.save()

    def test_normal_user(self):
        """Normal users allowed access."""
        user = User.objects.create_user('testuser', 'email@example.com',
                                        'testpass')
        user.save()
        self.client.force_login(user)

        response = self.client.get(teams_url)
        self.assertEqual(200, response.status_code)

    def test_no_users(self):
        """No users results in empty list, no superusers."""
        response = self.client.get(teams_url)
        self.assertEqual(200, response.status_code)

        self.assertEqual([], json.loads(response.content))

    def test_post(self):
        """POST not allowed"""
        response = self.client.post(teams_url)
        self.assertEqual(405, response.status_code)

    def test_correct_json(self):
        """Response JSON is properly formatted."""
        self.create_data()

        response = self.client.get(teams_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(2, len(data))

        for user in data:
            self.assertIn('team', user)
            self.assertIn('id', user['team'])
            self.assertIn('username', user['team'])
            self.assertIn('inAir', user)
            if 'telemetry' in user:
                self.assertIn('telemetryId', user)
                self.assertIn('telemetryAgeSec', user)
                self.assertIn('telemetryTimestamp', user)

    def test_users_correct(self):
        """User names and status correct."""
        self.create_data()

        response = self.client.get(teams_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        names = [d['team']['username'] for d in data]
        self.assertIn('user1', names)
        self.assertIn('user2', names)

        user1 = data[names.index('user1')]
        self.assertEqual(True, user1['inAir'])
        self.assertNotIn('telemetry', user1)

        user2 = data[names.index('user2')]
        self.assertEqual(False, user2['inAir'])
        self.assertEqual(
            {
                u'latitude': 38.6462,
                u'longitude': -76.2452,
                u'altitude': 0.0,
                u'heading': 90.0,
            }, user2['telemetry'])
        self.assertEqual(int(user2['telemetryId']), self.telem.pk)
        self.assertGreater(user2['telemetryAgeSec'], 0)
        self.assertEqual(user2['telemetryTimestamp'],
                         u'2016-10-01T00:00:00+00:00')


class TestTeamViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.get(team_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestTeamView(TestCase):
    """Tests the teams-by-id view."""
    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'email@example.com',
                                              'testpass')
        self.user1.save()

        self.superuser = User.objects.create_superuser('superuser',
                                                       'email@example.com',
                                                       'superpass')
        self.superuser.save()
        self.client.force_login(self.superuser)

    def test_bad_id(self):
        """Invalid user id rejected"""
        response = self.client.get(team_url(args=[999]))
        self.assertGreaterEqual(400, response.status_code)

    def test_correct_user(self):
        """User requested is correct"""
        response = self.client.get(team_url(args=[self.user1.username]))
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)
        self.assertIn('team', data)
        self.assertIn('username', data['team'])
        self.assertEqual('user1', data['team']['username'])
        self.assertIn('inAir', data)
        self.assertEqual(False, data['inAir'])
        self.assertNotIn('telemetry', data)

    def test_post(self):
        """POST not allowed"""
        response = self.client.post(team_url(args=[self.user1.username]))
        self.assertEqual(405, response.status_code)
