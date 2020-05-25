# Module to receive MAVLink packets and forward telemetry via interoperability.
# Packet details at http://mavlink.org/messages/common#GLOBAL_POSITION_INT.

import logging
import threading
import time

from auvsi_suas.proto.interop_api_pb2 import Telemetry
from pymavlink import mavutil

logger = logging.getLogger(__name__)


class MavlinkProxy(object):
    """Proxies mavlink packets to the interop server.

    Uses an asynchronous client to enable multiple telemetry to be concurrently
    forwarded so throughput is limited by RTT of the request. Prints request
    rate.
    """
    def __init__(self, device, client):
        """Receives telemetry over the device and forwards via the client.

        Args:
            device: A pymavlink device name to forward.
            client: Interop Client with which to send telemetry packets.
        """
        self.client = client
        # Create mavlink connection.
        self.mav = mavutil.mavlink_connection(device, autoreconnect=True)
        # Protects concurrent access to state.
        self.state_lock = threading.Lock()
        # Track rate of requests.
        self.sent_since_print = 0
        self.last_print = time.time()
        self.healthy = True
        # Periodically print rates.
        self.print_timer = threading.Timer(5.0, self._print_state)
        self.print_timer.start()

    def proxy(self):
        """Continuously proxy telemetry until an error."""
        while True:
            # Check healthiness.
            with self.state_lock:
                if not self.healthy:
                    return
            # Get packet.
            msg = self.mav.recv_match(type='GLOBAL_POSITION_INT',
                                      blocking=True,
                                      timeout=10.0)
            if msg is None:
                logger.critical(
                    'Did not receive MAVLink packet for over 10 seconds.')
                return
            # Convert to telemetry.
            telemetry = Telemetry()
            telemetry.latitude = self._mavlink_latlon(msg.lat)
            telemetry.longitude = self._mavlink_latlon(msg.lon)
            telemetry.altitude = self._mavlink_alt(msg.alt)
            telemetry.heading = self._mavlink_heading(msg.hdg)
            # Forward via client.
            self.client.post_telemetry(telemetry).add_done_callback(
                self._send_done)

    def _send_done(self, future):
        """Callback executed after telemetry post done."""
        try:
            future.result()
            with self.state_lock:
                self.sent_since_print += 1
        except:
            logger.exception('Failed to post telemetry to interop.')
            with self.state_lock:
                self.healthy = False

    def _print_state(self):
        now = time.time()
        with self.state_lock:
            since_print = now - self.last_print
            logger.info('Telemetry rate: %f',
                        self.sent_since_print / since_print)
            self.sent_since_print = 0
            self.last_print = now

    @classmethod
    def _mavlink_latlon(cls, degrees):
        """Converts a MAVLink packet lat/lon degree format to decimal degrees."""
        return float(degrees) / 1e7

    @classmethod
    def _mavlink_alt(cls, dist):
        """Converts a MAVLink packet millimeter format to decimal feet."""
        return dist * 0.00328084

    @classmethod
    def _mavlink_heading(cls, heading):
        """Converts a MAVLink packet heading format to decimal degrees."""
        return heading / 100.0
