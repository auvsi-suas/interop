# Module to receive MAVLink packets and forward telemetry via interoperability.
# Packet details at http://mavlink.org/messages/common#GLOBAL_POSITION_INT.

import logging
import sys
import time
from pymavlink import mavutil

from interop import Telemetry

logger = logging.getLogger(__name__)

PRINT_PERIOD = 5.0


def mavlink_latlon(degrees):
    """Converts a MAVLink packet lat/lon degree format to decimal degrees."""
    return float(degrees) / 1e7


def mavlink_alt(dist):
    """Converts a MAVLink packet millimeter format to decimal feet."""
    return dist * 0.00328084


def mavlink_heading(heading):
    """Converts a MAVLink packet heading format to decimal degrees."""
    return heading / 100.0


def proxy_mavlink(device, client):
    """Receives packets over the device and forwards telemetry via the client.

    Args:
        device: A pymavlink device name to forward.
        client: Interop Client with which to send telemetry packets.
    """
    # Create the MAVLink connection.
    mav = mavutil.mavlink_connection(device, autoreconnect=True)

    # Track rates.
    sent_since_print = 0
    last_print = time.time()

    # Continuously forward packets.
    while True:
        # Get packet.
        msg = mav.recv_match(type='GLOBAL_POSITION_INT',
                             blocking=True,
                             timeout=10.0)
        if msg is None:
            logger.critical(
                'Did not receive MAVLink packet for over 10 seconds.')
            sys.exit(-1)
        # Convert to telemetry.
        telemetry = Telemetry(latitude=mavlink_latlon(msg.lat),
                              longitude=mavlink_latlon(msg.lon),
                              altitude_msl=mavlink_alt(msg.alt),
                              uas_heading=mavlink_heading(msg.hdg))
        # Forward telemetry.
        try:
            client.post_telemetry(telemetry)
        except:
            logger.exception('Failed to post telemetry to interop.')
            sys.exit(-1)
        # Track telemetry rates.
        sent_since_print += 1
        now = time.time()
        since_print = now - last_print
        if since_print > PRINT_PERIOD:
            logger.info('Telemetry rate: %f', sent_since_print / since_print)
            sent_since_print = 0
            last_print = now
