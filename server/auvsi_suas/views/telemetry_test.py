"""Tests for the telemetry module."""

import datetime
import iso8601
import json
import time
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.uas_telemetry import UasTelemetry
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

login_url = reverse('auvsi_suas:login')
telemetry_url = reverse('auvsi_suas:telemetry')


class TestTelemetryViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.get(telemetry_url)
        self.assertEqual(403, response.status_code)


class TestTelemetryPost(TestCase):
    """Tests the Telemetry view POST."""

    def setUp(self):
        """Sets up the client, server info URL, and user."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()

        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

    def test_invalid_request(self):
        """Tests an invalid request by mis-specifying parameters."""
        response = self.client.post(telemetry_url)
        self.assertEqual(400, response.status_code)

        response = self.client.post(telemetry_url, {
            'longitude': 0,
            'altitude_msl': 0,
            'uas_heading': 0,
        })
        self.assertEqual(400, response.status_code)

        response = self.client.post(telemetry_url, {
            'latitude': 0,
            'altitude_msl': 0,
            'uas_heading': 0,
        })
        self.assertEqual(400, response.status_code)

        response = self.client.post(telemetry_url, {
            'latitude': 0,
            'longitude': 0,
            'uas_heading': 0,
        })
        self.assertEqual(400, response.status_code)

        response = self.client.post(telemetry_url, {
            'latitude': 0,
            'longitude': 0,
            'altitude_msl': 0,
        })
        self.assertEqual(400, response.status_code)

    def eval_request_values(self, lat, lon, alt, heading):
        response = self.client.post(telemetry_url, {
            'latitude': lat,
            'longitude': lon,
            'altitude_msl': alt,
            'uas_heading': heading
        })
        return response.status_code

    def test_invalid_request_values(self):
        """Tests by specifying correct parameters with invalid values."""
        TEST_DATA = [
            (-100, 0, 0, 0),
            (100, 0, 0, 0),
            (0, -190, 0, 0),
            (0, 190, 0, 0),
            (0, 0, 0, -10),
            (0, 0, 0, 370)
        ]  # yapf: disable
        for (lat, lon, alt, heading) in TEST_DATA:
            self.assertEqual(400,
                             self.eval_request_values(lat, lon, alt, heading))

    def test_upload_and_store(self):
        """Tests correct upload and storage of data."""
        lat = 10
        lon = 20
        alt = 30
        heading = 40
        response = self.client.post(telemetry_url, {
            'latitude': lat,
            'longitude': lon,
            'altitude_msl': alt,
            'uas_heading': heading
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(UasTelemetry.objects.all()), 1)
        obj = UasTelemetry.objects.all()[0]
        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.uas_heading, heading)
        self.assertEqual(obj.uas_position.altitude_msl, alt)
        self.assertEqual(obj.uas_position.gps_position.latitude, lat)
        self.assertEqual(obj.uas_position.gps_position.longitude, lon)

    def test_loadtest(self):
        """Tests the max load the view can handle."""
        if not settings.TEST_ENABLE_LOADTEST:
            return

        lat = 10
        lon = 20
        alt = 30
        heading = 40
        total_ops = 0
        start_t = time.clock()
        while time.clock() - start_t < settings.TEST_LOADTEST_TIME:
            self.client.post(telemetry_url, {
                'latitude': lat,
                'longiutde': lon,
                'altitude_msl': alt,
                'uas_heading': heading
            })
            total_ops += 1
        end_t = time.clock()
        total_t = end_t - start_t
        op_rate = total_ops / total_t

        print 'UAS Post Rate (%f)' % op_rate
        self.assertGreaterEqual(op_rate,
                                settings.TEST_LOADTEST_INTEROP_MIN_RATE)


class TestTelemetryGet(TestCase):
    """Test telemetry view GET."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            'superuser', 'email@example.com', 'superpass')
        self.superuser.save()

        self.user1 = User.objects.create_user('user1', 'email@example.com',
                                              'pass')

        self.user2 = User.objects.create_user('user2', 'email@example.com',
                                              'pass')

        self.year2000 = datetime.datetime(2000, 1, 1, tzinfo=timezone.utc)
        self.year2001 = datetime.datetime(2001, 1, 1, tzinfo=timezone.utc)
        self.year2002 = datetime.datetime(2002, 1, 1, tzinfo=timezone.utc)

        # Login
        response = self.client.post(login_url, {
            'username': 'superuser',
            'password': 'superpass'
        })
        self.assertEqual(200, response.status_code)

    def create_logs(self,
                    user,
                    num=10,
                    start=None,
                    delta=None,
                    altitude=100,
                    heading=90):
        if start is None:
            start = timezone.now()
        if delta is None:
            delta = datetime.timedelta(seconds=1)

        logs = []

        for i in xrange(num):
            gps = GpsPosition(latitude=38 + 0.001 * i,
                              longitude=-78 + 0.001 * i)
            gps.save()

            pos = AerialPosition(gps_position=gps, altitude_msl=altitude)
            pos.save()

            log = UasTelemetry(user=user,
                               uas_position=pos,
                               uas_heading=heading)
            log.save()
            log.timestamp = start + i * delta
            log.save()
            logs.append(log)

        return logs

    def test_normal_user(self):
        """Normal users not allowed access."""
        user = User.objects.create_user('testuser', 'email@example.com',
                                        'testpass')
        user.save()

        # Login
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

        response = self.client.get(telemetry_url)
        self.assertEqual(403, response.status_code)

    def test_no_telemetry(self):
        """No telemetry results in empty list."""
        response = self.client.get(telemetry_url)
        self.assertEqual(200, response.status_code)

        self.assertEqual([], json.loads(response.content))

    def test_basic(self):
        """Correct telemetry returned, with correct data."""
        telem = self.create_logs(self.user1,
                                 num=10,
                                 start=self.year2000,
                                 altitude=100,
                                 heading=90)

        response = self.client.get(telemetry_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(len(telem), len(data))

        lats = []
        lons = []
        times = []

        for entry in data:
            self.assertEqual(self.user1.pk, entry['user'])
            self.assertEqual(100, entry['altitude_msl'])
            self.assertEqual(90, entry['heading'])

            # All entries are unique
            self.assertNotIn(entry['timestamp'], times)
            times.append(entry['timestamp'])

            self.assertNotIn(entry['latitude'], lats)
            lats.append(entry['latitude'])

            self.assertNotIn(entry['longitude'], lons)
            lons.append(entry['longitude'])

    def test_default_limit(self):
        """Limit 100 by default"""
        telem = self.create_logs(self.user1, num=200)

        response = self.client.get(telemetry_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(100, len(data))

    def test_latest_first(self):
        """The latest telemetry is returned first."""
        telem = self.create_logs(self.user1, num=200)

        response = self.client.get(telemetry_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        expected_lats = [t.uas_position.gps_position.latitude for t \
                            in reversed(telem[100:])]

        actual_lats = [t['latitude'] for t in data]

        for i, actual_lat in enumerate(actual_lats):
            self.assertAlmostEqual(expected_lats[i], actual_lat)

    def test_invalid_limit(self):
        """Invalid limit parameter"""
        response = self.client.get(telemetry_url, {'limit': 'Hi!'})
        self.assertEqual(400, response.status_code)

    def test_limit(self):
        """Limit parameter"""
        telem = self.create_logs(self.user1, num=200)

        response = self.client.get(telemetry_url, {'limit': 10})
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(10, len(data))

    def test_invalid_user(self):
        """Invalid user parameter"""
        response = self.client.get(telemetry_url, {'user': 'Hi!'})
        self.assertEqual(400, response.status_code)

    def test_multi_user(self):
        """Logs from multiple users returned"""
        self.create_logs(self.user1, num=50)
        self.create_logs(self.user2, num=50)

        response = self.client.get(telemetry_url)
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(100, len(data))

    def test_user(self):
        """User parameter"""
        self.create_logs(self.user1, num=50)
        self.create_logs(self.user2, num=50)

        response = self.client.get(telemetry_url, {'user': self.user2.pk})
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(50, len(data))

        for entry in data:
            self.assertEqual(self.user2.pk, entry['user'])

    def test_invalid_since(self):
        """Invalid since parameter"""
        response = self.client.get(telemetry_url, {'since': 'June 1, 2000'})
        self.assertEqual(400, response.status_code)

    def test_since(self):
        """Logs since time (inclusive)."""
        self.create_logs(self.user1, num=50, start=self.year2000)
        self.create_logs(self.user1, num=50, start=self.year2001)

        response = self.client.get(telemetry_url, {
            'since': self.year2001.isoformat(),
        })
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        # since is non-inclusive, so the first entry is not included
        self.assertEqual(49, len(data))

        for entry in data:
            time = iso8601.parse_date(entry['timestamp'])
            self.assertGreater(time, self.year2001)

    def test_invalid_before(self):
        """Invalid before parameter"""
        response = self.client.get(telemetry_url, {'before': 'June 1, 2000'})
        self.assertEqual(400, response.status_code)

    def test_before(self):
        """Logs before time."""
        self.create_logs(self.user1, num=50, start=self.year2000)
        self.create_logs(self.user1, num=50, start=self.year2001)

        response = self.client.get(telemetry_url, {
            'before': self.year2001.isoformat(),
        })
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        self.assertEqual(50, len(data))

        for entry in data:
            time = iso8601.parse_date(entry['timestamp'])
            self.assertLess(time, self.year2001)

    def test_range(self):
        """Logs within range"""
        self.create_logs(self.user1, num=25, start=self.year2000)
        self.create_logs(self.user1, num=25, start=self.year2001)
        self.create_logs(self.user1, num=25, start=self.year2002)

        response = self.client.get(telemetry_url, {
            'since': self.year2001.isoformat(),
            'before': self.year2002.isoformat(),
        })
        self.assertEqual(200, response.status_code)

        data = json.loads(response.content)

        # since is non-inclusive, so the first entry is not included
        self.assertEqual(24, len(data))

        for entry in data:
            time = iso8601.parse_date(entry['timestamp'])
            self.assertGreater(time, self.year2001)
            self.assertLess(time, self.year2002)
