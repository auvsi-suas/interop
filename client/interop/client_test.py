import os
import dateutil.parser
import requests
import unittest

from . import Client, AsyncClient, InteropError, Telemetry

# These tests run against a real interop server.
# The server be loaded with the data from the test fixture in
# server/fixtures/test_fixture.yaml.

# Set these environmental variables to the proper values
# if the defaults are not correct.
server = os.getenv('TEST_INTEROP_SERVER', 'http://localhost')
username = os.getenv('TEST_INTEROP_USER', 'testuser')
password = os.getenv('TEST_INTEROP_PASS', 'testpass')


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
        self.client = Client(server, username, password)
        self.async_client = AsyncClient(server, username, password)

    def test_get_server_info(self):
        """Test getting server info."""
        info = self.client.get_server_info()
        async_info = self.async_client.get_server_info().result()

        # There isn't a whole lot to test. The fact that the call
        # didn't raise an exception is a good sign.
        self.assertEqual("Hello World!", info.message)
        self.assertEqual("Hello World!", async_info.message)

        expected_message_time = \
            dateutil.parser.parse('2015-08-02T01:16:15.609002+00:00')

        self.assertEqual(expected_message_time, info.message_timestamp)
        self.assertEqual(expected_message_time, async_info.message_timestamp)

        self.assertIsNotNone(info.server_time)
        self.assertIsNotNone(async_info.server_time)

    def test_post_telemetry(self):
        """Test sending some telemetry."""
        t = Telemetry(latitude=38.0,
                      longitude=-76.0,
                      altitude_msl=100.0,
                      uas_heading=90.0)

        # Raises an exception on error.
        self.client.post_telemetry(t)
        self.async_client.post_telemetry(t).result()

    def test_post_bad_telemetry(self):
        """Test sending some (incorrect) telemetry."""
        t0 = Telemetry(latitude=38.0,
                       longitude=-76.0,
                       altitude_msl=100.0,
                       uas_heading=90.0)
        # The Telemetry constructor prevents us from passing invalid
        # values, but we can still screw things up in an update
        t0 = t0._replace(latitude='baz')
        with self.assertRaises(InteropError):
            self.client.post_telemetry(t0)
        with self.assertRaises(InteropError):
            self.async_client.post_telemetry(t0).result()

        # We only accept Telemetry objects (or objects that behave like
        # Telemetry, not dicts.
        t1 = {
            'latitude': 38.0,
            'longitude': -76.0,
            'altitude_msl': 100.0,
            'uas_heading': 90.0
        }
        with self.assertRaises(AttributeError):
            self.client.post_telemetry(t1)
        with self.assertRaises(AttributeError):
            self.async_client.post_telemetry(t1).result()

    def test_get_obstacles(self):
        """Test getting obstacles."""
        stationary, moving = self.client.get_obstacles()
        async_future = self.async_client.get_obstacles()
        async_stationary, async_moving = async_future.result()

        # No exceptions is a good sign, let's see if the data matches the fixture.
        self.assertEqual(2, len(stationary))
        self.assertEqual(2, len(async_stationary))
        self.assertEqual(1, len(moving))
        self.assertEqual(1, len(async_moving))

        # Lat, lon, and altitude of the moving obstacles change, so we don't
        # check those.
        self.assertEqual(50.0, moving[0].sphere_radius)
        self.assertEqual(50.0, async_moving[0].sphere_radius)

        radii = [o.cylinder_radius for o in stationary]
        async_radii = [o.cylinder_radius for o in async_stationary]
        self.assertIn(50.0, radii)
        self.assertIn(50.0, async_radii)
        self.assertIn(150.0, radii)
        self.assertIn(150.0, async_radii)

        heights = [o.cylinder_height for o in stationary]
        self.assertIn(300.0, heights)
        self.assertIn(200.0, heights)
        async_heights = [o.cylinder_height for o in async_stationary]
        self.assertIn(300.0, async_heights)
        self.assertIn(200.0, async_heights)
