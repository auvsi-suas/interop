"""This file provides Python types for the client API.

Most of these types are direct copies of what the interop server API
requires. They include input validation, making a best-effort to ensure
values will be accepted by the server.
"""

import re
import sys


class ClientBaseType(object):
    """ ClientBaseType is a simple base class which provides basic functions.

    The attributes are obtained from the 'attrs' property, which should be
    defined by subclasses.
    """

    # Subclasses should override.
    attrs = []

    def __eq__(self, other):
        """Compares two objects."""
        for attr in self.attrs:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def __repr__(self):
        """Gets string encoding of object."""
        return "%s(%s)" % (self.__class__.__name__,
                           ', '.join('%s=%s' % (attr, self.__dict__[attr])
                                     for attr in self.attrs))

    def __unicode__(self):
        """Gets unicode encoding of object."""
        return unicode(self.__str__())

    def serialize(self):
        """Serialize the current state of the object."""
        serial = {}
        for attr in self.attrs:
            data = self.__dict__[attr]
            if isinstance(data, ClientBaseType):
                serial[attr] = data.serialize()
            elif isinstance(data, list):
                serial[attr] = [d.serialize() for d in data]
            elif data is not None:
                serial[attr] = data
        return serial

    @classmethod
    def deserialize(cls, d):
        """Deserialize the state of the object."""
        if isinstance(d, cls):
            return d
        else:
            return cls(**d)


class GpsPosition(ClientBaseType):
    """GPS position consisting of a latitude and longitude.

    Attributes:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.

    Raises:
        ValueError: Argument not convertable to float.
    """

    attrs = ['latitude', 'longitude']

    def __init__(self, latitude, longitude):
        self.latitude = float(latitude)
        self.longitude = float(longitude)


class FlyZone(ClientBaseType):
    """Flight boundary consisting of GPS polygon and altitude range.

    Attributes:
        boundary_pts: List of Waypoint defining a polygon.
        altitude_msl_min: Minimum altitude in feet MSL.
        altitude_msl_max: Maximum altitude in feet MSL.

    Raises:
        ValueError: Argument not convertable to float.
    """

    attrs = ['boundary_pts', 'altitude_msl_min', 'altitude_msl_max']

    def __init__(self, boundary_pts, altitude_msl_min, altitude_msl_max):
        self.boundary_pts = [Waypoint.deserialize(bp) for bp in boundary_pts]
        self.altitude_msl_min = float(altitude_msl_min)
        self.altitude_msl_max = float(altitude_msl_max)


class Waypoint(ClientBaseType):
    """Waypoint consisting of an order, GPS position, and optional altitude.

    Attributes:
        order: An ID giving relative order in a set of waypoints.
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        altitude: Optional. Altitude in feet MSL.

    Raises:
        ValueError: Argument not convertable to int or float.
    """

    attrs = ['order', 'latitude', 'longitude', 'altitude_msl']

    def __init__(self, order, latitude, longitude, altitude_msl=None):
        self.order = int(order)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.altitude_msl = None
        if altitude_msl is not None:
            self.altitude_msl = float(altitude_msl)


class Mission(ClientBaseType):
    """Mission details.

    Attributes:
        id: The unique ID of the mission.
        active: Whether the mission is active.
        air_drop_pos: The GpsPosition of the air drop.
        fly_zones: A list of FlyZone boundaries the UAS must be within.
        home_pos: The GpsPosition of the UAS launch point (tents).
        mission_waypoints: A list of Waypoint the UAS must traverse.
        off_axis_target_pos: The GpsPosition of the off-axis target.
        emergent_last_known_pos: The last known GpsPosition of the emergent
            target.
        search_grid_points: List of Waypoint defining the search grid polygon.

    Raises:
        ValueError: Argument not convertable to int or float.
    """

    attrs = ['id', 'active', 'air_drop_pos', 'fly_zones', 'home_pos',
             'mission_waypoints', 'off_axis_target_pos',
             'emergent_last_known_pos', 'search_grid_points']

    def __init__(self, id, active, air_drop_pos, fly_zones, home_pos,
                 mission_waypoints, off_axis_target_pos,
                 emergent_last_known_pos, search_grid_points):
        self.id = int(id)
        self.active = bool(active)
        self.air_drop_pos = GpsPosition.deserialize(air_drop_pos)
        self.fly_zones = [FlyZone.deserialize(fz) for fz in fly_zones]
        self.home_pos = GpsPosition.deserialize(home_pos)
        self.mission_waypoints = [Waypoint.deserialize(mw)
                                  for mw in mission_waypoints]
        self.off_axis_target_pos = GpsPosition.deserialize(off_axis_target_pos)
        self.emergent_last_known_pos = GpsPosition.deserialize(
            emergent_last_known_pos)
        self.search_grid_points = [Waypoint.deserialize(sg)
                                   for sg in search_grid_points]


class Telemetry(ClientBaseType):
    """UAS Telemetry at a single point in time.

    Attributes:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        altitude_msl: Altitude MSL in feet.
        uas_heading: Aircraft heading (true north) in degrees (0-360).

    Raises:
        ValueError: Argument not convertable to float.
    """

    attrs = ['latitude', 'longitude', 'altitude_msl', 'uas_heading']

    def __init__(self, latitude, longitude, altitude_msl, uas_heading):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.altitude_msl = float(altitude_msl)
        self.uas_heading = float(uas_heading)


class StationaryObstacle(ClientBaseType):
    """A stationary obstacle.

    This obstacle is a cylinder with a given location, height, and radius.

    Attributes:
        latitude: Latitude of the center of the cylinder in decimal degrees
        longitude: Longitude of the center of the cylinder in decimal degrees
        cylinder_radius: Radius in feet
        cylinder_height: Height in feet

    Raises:
        ValueError: Argument not convertable to float.
    """

    attrs = ['latitude', 'longitude', 'cylinder_radius', 'cylinder_height']

    def __init__(self, latitude, longitude, cylinder_radius, cylinder_height):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.cylinder_radius = float(cylinder_radius)
        self.cylinder_height = float(cylinder_height)


class MovingObstacle(ClientBaseType):
    """A moving obstacle.

    This obstacle is a sphere with a given location, altitude, and radius.

    Attributes:
        latitude: Latitude of the center of the cylinder in decimal degrees
        longitude: Longitude of the center of the cylinder in decimal degrees
        altitude_msl: Sphere centroid altitude MSL in feet
        sphere_radius: Radius in feet

    Raises:
        ValueError: Argument not convertable to float.
    """

    attrs = ['latitude', 'longitude', 'altitude_msl', 'sphere_radius']

    def __init__(self, latitude, longitude, altitude_msl, sphere_radius):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.altitude_msl = float(altitude_msl)
        self.sphere_radius = float(sphere_radius)


class Target(ClientBaseType):
    """A target.

    Attributes:
        id: Optional. The ID of the target. Assigned by the interoperability
            server.
        user: Optional. The ID of the user who created the target. Assigned by
            the interoperability server.
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
        autonomous: Optional; defaults to False. Indicates that this is an
            ADLC target.
        team_id: Optional. The username of the team on whose behalf to submit
            targets. Must be admin user to specify.
        actionable_override: Optional. Manually sets the target to be
            actionable. Must be admin user to specify.

    Raises:
        ValueError: Argument not valid.
    """

    attrs = ['id', 'user', 'type', 'latitude', 'longitude', 'orientation',
             'shape', 'background_color', 'alphanumeric', 'alphanumeric_color',
             'description', 'autonomous', 'team_id', 'actionable_override']

    def __init__(self,
                 id=None,
                 user=None,
                 type=None,
                 latitude=None,
                 longitude=None,
                 orientation=None,
                 shape=None,
                 background_color=None,
                 alphanumeric=None,
                 alphanumeric_color=None,
                 description=None,
                 autonomous=False,
                 team_id=None,
                 actionable_override=None):
        self.id = id
        self.user = user
        self.type = type
        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None
        self.orientation = orientation
        self.shape = shape
        self.background_color = background_color
        self.alphanumeric = alphanumeric
        self.alphanumeric_color = alphanumeric_color
        self.description = description
        self.autonomous = autonomous
        self.actionable_override = actionable_override
        self.team_id = team_id
