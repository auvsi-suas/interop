import os
import subprocess
import time
import unittest
from pymavlink import mavutil


class InteropCliTestBase(unittest.TestCase):
    """Base for tests."""
    def setUp(self):
        """Setup the CLI path and base args."""
        self.cli_path = os.path.join(os.path.dirname(__file__),
                                     "interop_cli.py")
        self.cli_base_args = [
            self.cli_path, '--url', 'http://localhost:8000', '--username',
            'testuser', '--password', 'testpass'
        ]

    def assertCliOk(self, args):
        """Asserts that the CLI command succeeds."""
        self.assertEqual(0, subprocess.call(args))


class TestTeams(InteropCliTestBase):
    """Test able to request statuses of teams."""
    def test_get_teams(self):
        """Test getting statuses of teams."""
        self.assertCliOk(self.cli_base_args + ['teams'])


class TestMissions(InteropCliTestBase):
    """Test able to request mission details."""
    def test_get_mission(self):
        """Test getting mission details."""
        self.assertCliOk(self.cli_base_args + ['mission', '--mission_id', '1'])


class TestOdlcs(InteropCliTestBase):
    """Test able to upload odlcs."""
    def setUp(self):
        """Compute the testdata folder."""
        super(TestOdlcs, self).setUp()
        self.odlc_dir = os.path.join(os.path.dirname(__file__), "testdata")

    def test_get_odlcs(self):
        """Test getting odlcs."""
        self.assertCliOk(self.cli_base_args + ['odlcs'])
        self.assertCliOk(self.cli_base_args + ['odlcs', '--mission_id', '1'])

    def test_upload_odlcs(self):
        """Test uploading odlcs with Object File Format."""
        self.assertCliOk(self.cli_base_args +
                         ['odlcs', '--odlc_dir', self.odlc_dir])


class TestProbe(InteropCliTestBase):
    """Test able to probe server."""
    def setUp(self):
        """Setup process to probe server."""
        super(TestProbe, self).setUp()
        self.probe = subprocess.Popen(self.cli_base_args + ['probe'])

    def tearDown(self):
        """Terminate if a running process."""
        self.probe.poll()
        if self.probe.returncode is None:
            self.probe.terminate()

    def assertProbeAlive(self):
        """Assert probe still running."""
        self.probe.poll()
        self.assertIsNone(self.probe.returncode)

    def test_probe(self):
        """Ensure probe lasts for at least 5s."""
        start = time.time()
        while time.time() - start < 5:
            self.assertProbeAlive()
            time.sleep(0.1)


class TestMavlink(InteropCliTestBase):
    """Tests proxying MAVLink packets."""
    def setUp(self):
        """Creates a playback and forward of MAVLink packets."""
        super(TestMavlink, self).setUp()
        # Create input and output logs to simulate a source.
        log_filepath = os.path.join(os.path.dirname(__file__),
                                    "testdata/mav.tlog")
        self.mlog = mavutil.mavlink_connection(log_filepath)
        self.mout = mavutil.mavlink_connection('127.0.0.1:14550', input=False)
        # Start the forwarding on the CLI.
        self.forward = subprocess.Popen(
            self.cli_base_args + ['mavlink', '--device', '127.0.0.1:14550'])
        time.sleep(1)  # Allow time to start forward.

    def tearDown(self):
        """Stops any subprocesses."""
        self.forward.poll()
        if self.forward.returncode is None:
            self.forward.terminate()

    def assertForwardAlive(self):
        """Asserts the forward process is alive."""
        self.forward.poll()
        self.assertIsNone(self.forward.returncode)

    def test_proxy(self):
        """Checks that proxying doesn't die."""
        # Forward all proxy messages.
        while True:
            self.assertForwardAlive()
            msg = self.mlog.recv_match()
            if msg is None:
                break
            self.mout.write(msg.get_msgbuf())
        # Ensure proxy still alive for 5s.
        start = time.time()
        while time.time() - start < 5:
            self.assertForwardAlive()
            time.sleep(0.1)
