import os
import requests
import unittest

from auvsi_suas.client.client import AsyncClient
from auvsi_suas.client.client import Client
from auvsi_suas.client.exceptions import InteropError
from auvsi_suas.proto import interop_api_pb2

# These tests run against a real interop server.
# The server be loaded with the data from the test fixture in
# server/fixtures/test_fixture.yaml.

# Set these environmental variables to the proper values
# if the defaults are not correct.
server = os.getenv('TEST_INTEROP_SERVER', 'http://localhost:8000')
username = os.getenv('TEST_INTEROP_USER', 'testuser')
password = os.getenv('TEST_INTEROP_USER_PASS', 'testpass')
admin_username = os.getenv('TEST_INTEROP_ADMIN', 'testadmin')
admin_password = os.getenv('TEST_INTEROP_ADMIN_PASS', 'testpass')


class TestClientLoggedOut(unittest.TestCase):
    """Test the portions of the Client class used before login."""
    def test_login(self):
        """Simple login test."""
        # Simply creating a Client causes a login.
        # If it doesn't raise an exception, it worked!
        Client(server, username, password)
        AsyncClient(server, username, password)

    def test_bad_login(self):
        """Bad login raises exception"""
        with self.assertRaises(InteropError):
            Client(server, "foo", "bar")
        with self.assertRaises(InteropError):
            AsyncClient(server, "foo", "bar")

    def test_timeout(self):
        """Test connection timeout"""
        # We are assuming that there is no machine at this address.
        addr = "http://10.255.255.254"
        timeout = 0.0001
        with self.assertRaises(requests.Timeout):
            Client(addr, username, password, timeout=timeout)
        with self.assertRaises(requests.Timeout):
            AsyncClient(addr, username, password, timeout=timeout)


class TestClient(unittest.TestCase):
    """Test the Client class.
    The Client class is a very thin wrapper, so there is very little to test.
    """
    def setUp(self):
        """Create a logged in Client."""
        # Test rest with non-admin clients.
        self.client = Client(server, username, password)
        self.async_client = AsyncClient(server, username, password)

    def test_get_teams(self):
        """Tests getting team status."""
        teams = self.client.get_teams()
        async_teams = self.async_client.get_teams().result()
        self.assertEqual(1, len(teams))
        self.assertEqual(1, len(async_teams))
        self.assertEqual('testuser', teams[0].team.username)
        self.assertEqual('testuser', async_teams[0].team.username)

    def test_get_mission(self):
        """Test getting a mission."""
        mission = self.client.get_mission(1)
        async_mission = self.async_client.get_mission(1).result()

        # Check basic field info.
        self.assertEqual(1, mission.id)
        self.assertEqual(1, async_mission.id)

    def test_post_telemetry(self):
        """Test sending some telemetry."""
        t = interop_api_pb2.Telemetry()
        t.latitude = 38
        t.longitude = -76
        t.altitude = 100
        t.heading = 90

        # Raises an exception on error.
        self.client.post_telemetry(t)
        self.async_client.post_telemetry(t).result()

    def test_post_bad_telemetry(self):
        """Test sending some (incorrect) telemetry."""
        t = interop_api_pb2.Telemetry()
        t.latitude = 38
        t.longitude = -76
        t.altitude = 100
        t.heading = 400  # Out of range.
        with self.assertRaises(InteropError):
            self.client.post_telemetry(t)
        with self.assertRaises(InteropError):
            self.async_client.post_telemetry(t).result()

    def test_odlcs(self):
        """Test odlc workflow."""
        # Post a odlc gets an updated odlc.
        odlc = interop_api_pb2.Odlc()
        odlc.mission = 1
        odlc.type = interop_api_pb2.Odlc.STANDARD
        post_odlc = self.client.post_odlc(odlc)
        async_post_odlc = self.async_client.post_odlc(odlc).result()

        self.assertIsNotNone(post_odlc.id)
        self.assertIsNotNone(async_post_odlc.id)
        self.assertEqual(1, post_odlc.mission)
        self.assertEqual(1, async_post_odlc.mission)
        self.assertEqual(interop_api_pb2.Odlc.STANDARD, post_odlc.type)
        self.assertEqual(interop_api_pb2.Odlc.STANDARD, async_post_odlc.type)
        self.assertNotEqual(post_odlc.id, async_post_odlc.id)

        # Get odlc.
        get_odlc = self.client.get_odlc(post_odlc.id)
        async_get_odlc = self.async_client.get_odlc(
            async_post_odlc.id).result()
        get_odlcs = self.client.get_odlcs()
        async_get_odlcs = self.async_client.get_odlcs().result()
        get_odlcs_mission = self.client.get_odlcs(mission=1)
        async_get_odlcs_mission = self.async_client.get_odlcs(
            mission=1).result()
        get_odlcs_bad_mission = self.client.get_odlcs(mission=2)
        async_get_odlcs_bad_mission = self.async_client.get_odlcs(
            mission=2).result()

        self.assertEquals(post_odlc, get_odlc)
        self.assertEquals(async_post_odlc, async_get_odlc)
        self.assertIn(post_odlc, get_odlcs)
        self.assertIn(async_post_odlc, async_get_odlcs)
        self.assertIn(post_odlc, get_odlcs_mission)
        self.assertIn(async_post_odlc, async_get_odlcs_mission)
        self.assertNotIn(post_odlc, get_odlcs_bad_mission)
        self.assertNotIn(async_post_odlc, async_get_odlcs_bad_mission)

        # Update odlc.
        post_odlc.shape = interop_api_pb2.Odlc.CIRCLE
        async_post_odlc.shape = interop_api_pb2.Odlc.CIRCLE
        put_odlc = self.client.put_odlc(post_odlc.id, post_odlc)
        async_put_odlc = self.async_client.put_odlc(async_post_odlc.id,
                                                    async_post_odlc).result()

        self.assertEquals(post_odlc, put_odlc)
        self.assertEquals(async_post_odlc, async_put_odlc)

        # Upload odlc image.
        test_image_filepath = os.path.join(os.path.dirname(__file__),
                                           "testdata/A.jpg")
        with open(test_image_filepath, 'rb') as f:
            image_data = f.read()
        self.client.put_odlc_image(post_odlc.id, image_data)
        self.async_client.put_odlc_image(async_post_odlc.id,
                                         image_data).result()

        # Get the odlc image.
        get_image = self.client.get_odlc_image(post_odlc.id)
        async_get_image = self.async_client.get_odlc_image(
            async_post_odlc.id).result()
        self.assertEquals(image_data, get_image)
        self.assertEquals(image_data, async_get_image)

        # Delete the odlc image.
        self.client.delete_odlc_image(post_odlc.id)
        self.async_client.delete_odlc_image(async_post_odlc.id).result()
        with self.assertRaises(InteropError):
            self.client.get_odlc_image(post_odlc.id)
        with self.assertRaises(InteropError):
            self.async_client.get_odlc_image(async_post_odlc.id).result()

        # Delete odlc.
        self.client.delete_odlc(post_odlc.id)
        self.async_client.delete_odlc(async_post_odlc.id).result()

        self.assertNotIn(post_odlc, self.client.get_odlcs())
        self.assertNotIn(async_post_odlc,
                         self.async_client.get_odlcs().result())

    def test_map(self):
        """Test map workflow."""
        test_image_filepath = os.path.join(os.path.dirname(__file__),
                                           "testdata/A.jpg")
        with open(test_image_filepath, 'rb') as f:
            image_data = f.read()

        self.client.put_map_image(1, image_data)
        get_image = self.client.get_map_image(1)
        self.assertEqual(image_data, get_image)
        self.client.delete_map_image(1)

        self.async_client.put_map_image(1, image_data).result()
        get_image = self.async_client.get_map_image(1).result()
        self.assertEqual(image_data, get_image)
        self.async_client.delete_map_image(1).result()
