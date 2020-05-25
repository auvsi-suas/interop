"""Tests for the telemetry module."""

import time
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.proto.interop_api_pb2 import Telemetry
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from google.protobuf import json_format

telemetry_url = reverse('auvsi_suas:telemetry')


class TestTelemetryViewLoggedOut(TestCase):
    def test_not_authenticated(self):
        """Tests requests that have not yet been authenticated."""
        response = self.client.post(telemetry_url)
        self.assertEqual(403, response.status_code)


class TestTelemetryPost(TestCase):
    """Tests the Telemetry view POST."""

    def setUp(self):
        """Sets up the client, server info URL, and user."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()
        self.client.force_login(self.user)

    def telemetry_request(self, lat=None, lon=None, alt=None, head=None):
        proto = Telemetry()
        if lat is not None:
            proto.latitude = lat
        if lon is not None:
            proto.longitude = lon
        if alt is not None:
            proto.altitude = alt
        if head is not None:
            proto.heading = head
        proto_json = json_format.MessageToJson(proto)

        return self.client.post(
            telemetry_url, data=proto_json, content_type='application/json')

    def test_invalid_request(self):
        """Tests an invalid request by mis-specifying parameters."""
        response = self.client.post(telemetry_url)
        self.assertEqual(400, response.status_code)

        response = self.telemetry_request(lon=0, alt=0, head=0)
        self.assertEqual(400, response.status_code)

        response = self.telemetry_request(lat=0, alt=0, head=0)
        self.assertEqual(400, response.status_code)

        response = self.telemetry_request(lat=0, lon=0, head=0)
        self.assertEqual(400, response.status_code)

        response = self.telemetry_request(lat=0, lon=0, alt=0)
        self.assertEqual(400, response.status_code)

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
        for (lat, lon, alt, head) in TEST_DATA:
            self.assertEqual(400,
                             self.telemetry_request(lat, lon, alt,
                                                    head).status_code)

    def test_upload_and_store(self):
        """Tests correct upload and storage of data."""
        response = self.telemetry_request(lat=10, lon=20, alt=30, head=40)
        self.assertEqual(200, response.status_code, response.content)
        self.assertEqual(len(UasTelemetry.objects.all()), 1)
        obj = UasTelemetry.objects.all()[0]
        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.latitude, 10)
        self.assertEqual(obj.longitude, 20)
        self.assertEqual(obj.altitude_msl, 30)
        self.assertEqual(obj.uas_heading, 40)

    def test_loadtest(self):
        """Tests the max load the view can handle."""
        total_ops = 100
        start_t = time.perf_counter()
        for _ in range(total_ops):
            response = self.telemetry_request(lat=10, lon=20, alt=30, head=40)
            self.assertEqual(200, response.status_code)
        end_t = time.perf_counter()
        op_rate = total_ops / (end_t - start_t)
        self.assertGreaterEqual(op_rate, 20)
