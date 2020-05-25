"""Tests for the login module."""

from auvsi_suas.proto.interop_api_pb2 import Credentials
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from google.protobuf import json_format

login_url = reverse('auvsi_suas:login')


class TestLoginUserView(TestCase):
    """Tests the login_user view."""

    def setUp(self):
        """Sets up the test by creating a test user."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()

    def login_request_body(self, username=None, password=None):
        request_proto = Credentials()
        if username:
            request_proto.username = username
        if password:
            request_proto.password = password
        return json_format.MessageToJson(request_proto)

    def test_invalid_request(self):
        """Tests an invalid request by mis-specifying parameters."""
        # Test GET instead of POST
        response = self.client.get(login_url)
        self.assertEqual(405, response.status_code)

        # Test POST with no parameters
        response = self.client.post(login_url)
        self.assertEqual(400, response.status_code)

        # Test POST with a missing parameter
        response = self.client.post(
            login_url,
            data=self.login_request_body('testuser'),
            content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.client.post(
            login_url,
            data=self.login_request_body(password='testpass'),
            content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_invalid_credentials(self):
        """Tests invalid credentials for login."""
        response = self.client.post(
            login_url,
            data=self.login_request_body('testuser', 'invalidpass'),
            content_type='application/json')
        self.assertEqual(401, response.status_code)

    def test_correct_credentials(self):
        """Tests correct credentials for login."""
        response = self.client.post(
            login_url,
            data=self.login_request_body('testuser', 'testpass'),
            content_type='application/json')
        self.assertEqual(200, response.status_code)
