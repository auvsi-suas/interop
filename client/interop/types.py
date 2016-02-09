"""This file provides Python types for the client API.

Most of these types are direct copies of what the interop server API
requires. They include input validation, making a best-effort to ensure
values will be accepted by the server.
"""

from collections import namedtuple
from collections import OrderedDict
import dateutil.parser
import re
import sys


def check_type(obj, obj_type):
    """Asserts that the obj is of the given type.

    Raises:
        ValueError: Invalid type.
    """
    if not isinstance(obj, obj_type):
        raise ValueError('Object (%s) is not the type %s' % (obj, obj_type))


def check_bounds(value, min_value, max_value):
    """Assert that the given value is within the range.

    Raises:
        ValueError: Out of range.
    """
    if value < min_value or value > max_value:
        raise ValueError('Value (%f) out of range [%f, %f]' %
                         (value, min_value, max_value))


def check_latitude(lat):
    """Assert that latitude is valid.

    Raises:
        ValueError: Latitude out of range.
    """
    check_bounds(lat, -90, 90)


def check_longitude(lon):
    """Assert that longitude is valid.

    Raises:
        ValueError: Longitude out of range.
    """
    check_bounds(lon, -180, 180)


def check_heading(heading):
    """Asserts that heading is valid.

    Raises:
        ValueError: Heading out of range.
    """
    check_bounds(heading, 0, 360)


class Telemetry(
        namedtuple('Telemetry',
                   ['latitude', 'longitude', 'altitude_msl', 'uas_heading'])):
    """UAS Telemetry at a single point in time.

    Attributes:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        altitude_msl: Altitude MSL in feet.
        uas_heading: Aircraft heading in degrees [0, 360].

    Raises:
        ValueError: Argument not valid.
    """

    def __init__(self, *args, **kwargs):
        check_type(self.latitude, float)
        check_type(self.longitude, float)
        check_type(self.altitude_msl, float)
        check_type(self.uas_heading, float)

        check_latitude(self.latitude)
        check_longitude(self.longitude)
        check_heading(self.uas_heading)

    def _asdict(self):
        return OrderedDict(zip(self._fields, self))


class ServerInfo(namedtuple('ServerInfo',
                            ['message', 'message_timestamp', 'server_time'])):
    """Server information to be displayed to judges.

    Attributes:
        message: Custom message from the server
        message_timestamp (datetime.datetime): Message timestamp
        server_time (datetime.datetime): Current server time

    Raises:
        TypeError, ValueError: Message or server timestamp could not be parsed.
    """

    def __new__(cls, message, message_timestamp, server_time):
        return super(ServerInfo, cls).__new__(
            cls,
            message=message,
            message_timestamp=dateutil.parser.parse(message_timestamp),
            server_time=dateutil.parser.parse(server_time))


class StationaryObstacle(namedtuple('StationaryObstacle',
                                    ['latitude', 'longitude',
                                     'cylinder_height', 'cylinder_radius'])):
    """A stationary obstacle.

    This obstacle is a cylinder with a given location, height, and radius.

    Attributes:
        latitude: Latitude of the center of the cylinder in decimal degrees
        longitude: Longitude of the center of the cylinder in decimal degrees
        cylinder_radius: Radius in feet
        cylinder_height: Height in feet

    Raises:
        ValueError: Argument not valid.
    """

    def __init__(self, *args, **kwargs):
        check_type(self.latitude, float)
        check_type(self.longitude, float)
        check_type(self.cylinder_radius, float)
        check_type(self.cylinder_height, float)

        check_latitude(self.latitude)
        check_longitude(self.longitude)

        check_bounds(self.cylinder_radius, 0, float("inf"))
        check_bounds(self.cylinder_height, 0, float("inf"))


class MovingObstacle(namedtuple(
        'MovingObstacle',
    ['latitude', 'longitude', 'altitude_msl', 'sphere_radius'])):
    """A moving obstacle.

    This obstacle is a sphere with a given location, altitude, and radius.

    Attributes:
        latitude: Latitude of the center of the cylinder in decimal degrees
        longitude: Longitude of the center of the cylinder in decimal degrees
        altitude_msl: Sphere centroid altitude MSL in feet
        sphere_radius: Radius in feet

    Raises:
        ValueError: Argument not valid.
    """

    def __init__(self, *args, **kwargs):
        check_type(self.latitude, float)
        check_type(self.longitude, float)
        check_type(self.altitude_msl, float)
        check_type(self.sphere_radius, float)

        check_latitude(self.latitude)
        check_longitude(self.longitude)

        check_bounds(self.sphere_radius, 0, float("inf"))


class Target(namedtuple(
        'Target', ['id', 'user', 'type', 'latitude', 'longitude',
                   'orientation', 'shape', 'background_color', 'alphanumeric',
                   'alphanumeric_color', 'description'])):
    """A target.

    Attributes:
        id: Optional. The ID of the target, assigned by interoperability
            server. New targets shouldn't define this field.
        user: Optional. The ID of the user who created the target, assigned by
            interoperability server. New targets shouldn't define this field.
        type: Target type, must be one of TargetType.
        latitude: Optional. Target latitude in decimal degrees. If provided,
            longitude must also be provided.
        longitude: Optional. Target longitude in decimal degrees. If provided,
            latitude must also be provided.
        orientation: Optional. Target orientation.
        shape: Optional. Target shape.
        background_color: Optional. Target color.
        alphanumeric: Optional. Target alphanumeric. [0-9, a-z, A-Z].
        alphanumeric_color: Optional. Target alphanumeric color.
        description: Optional. Free-form description of the target, used for
            certain target types.

    Raises:
        ValueError: Argument not valid.
    """

    def __new__(cls, *args, **kwargs):
        for field in cls._fields:
            if field not in kwargs:
                kwargs[field] = None
        return super(Target, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        check_type(self.type, str)
        check_type(self.latitude, float)
        check_type(self.longitude, float)

        check_latitude(self.latitude)
        check_longitude(self.longitude)

        if (self.alphanumeric and
                not re.match('^[0-9a-zA-Z]$', self.alphanumeric)):
            raise ValueError('Provided alphanumeric is not valid: %s' %
                             self.alphanumeric)

    def _asdict(self):
        return OrderedDict(zip(self._fields, self))
