"""Functions for computing distance."""

import math
import numpy as np
import pyproj
from django.conf import settings
from auvsi_suas.models import units

wgs84 = pyproj.Proj(init="epsg:4326")


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).

    Reference:
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points

    Args:
        lon1, lat1: The latitude and longitude of position 1
        lon2, lat2: The latitude and longitude of position 2

    Returns:
        The distance in kilometers
    """
    # convert decimal degrees to radians
    lon1 = math.radians(lon1)
    lat1 = math.radians(lat1)
    lon2 = math.radians(lon2)
    lat2 = math.radians(lat2)

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    hav_a = (math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) *
             math.sin(dlon / 2)**2)
    hav_c = 2 * math.asin(math.sqrt(hav_a))

    # 6367 km is the radius of the Earth
    dist_km = 6371 * hav_c
    return dist_km


def distance_to(latitude_1, longitude_1, altitude_1, latitude_2, longitude_2,
                altitude_2):
    """Get the distance in feet between the two positions.

    Args:
        latitude_1: The latitude of the first position.
        longitude_1: The longitude of the first position.
        altitude_1: The altitude in feet of the first position.
        latitude_2: The latitude of the second position.
        longitude_2: The longitude of the second position.
        altitude_2: The altitude in feet of the second position.
    """
    gps_dist_km = haversine(longitude_1, latitude_1, longitude_2, latitude_2)
    gps_dist_ft = units.kilometers_to_feet(gps_dist_km)
    alt_dist_ft = abs(altitude_1 - altitude_2)
    return math.hypot(gps_dist_ft, alt_dist_ft)


def utm_zone(lat, lon):
    """Determine the UTM zone for a given latitude and longitude.

    Based on http://gis.stackexchange.com/a/13292

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        zone number: UTM zone number lat/lon falls in
        north: bool indicating North/South
    """
    zone = math.floor((lon + 180) / 6.0) + 1

    # Special cases for Norway and Svalbard
    if lat >= 56 and lat < 64 and lon >= 3 and lon < 12:
        zone = 32

    if lat >= 72 and lat < 84:
        if lon >= 0 and lon < 9:
            zone = 31
        elif lon >= 9 and lon < 21:
            zone = 33
        elif lon >= 21 and lon < 33:
            zone = 35
        elif lon >= 33 and lon < 42:
            zone = 37

    return zone, lat > 0


def proj_utm(zone, north):
    """Proj instance for the given zone.

    Args:
        zone: UTM zone
        north: North zone or south zone

    Returns:
        pyproj.Proj instance for the given zone
    """
    ref = "+proj=utm +zone=%d +ellps=WGS84" % zone
    if not north:
        ref += " +south"
    return pyproj.Proj(ref)


def distance_to_line(start, end, point, utm):
    """Compute the closest distance from point to a line segment.

    Based on the point-line distance derived in:
    http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html

          (l_1 - p) dot (l_2 - p)
    t = - -----------------------
               |l_2 - l_1|^2

    We clamp t to 0 <= t <= 1 to ensure we calculate distance to a point on
    the line segment.

    The closest point can be determined using t:

    p_c = l_1 + t * (l_2 - l_1)

    And the distance is:

    d = |p - p_c|

    Arguments are points in the form (lat, lon, alt MSL (ft)).

    Args:
        start: Defines the start of the line.
        end: Defines the end of the line.
        point: Free point to compute distance from.
        utm: The UTM Proj projection to project into. If start, end, or point
             are well outside of this projection, this function returns
             infinite.

    Returns:
        Closest distance in ft from point to the line.
    """
    try:
        # Convert points to UTM projection.
        # We need a cartesian coordinate system to perform the calculation.
        lat, lon, ftmsl = start
        x, y = pyproj.transform(wgs84, utm, lon, lat)
        l1 = np.array([x, y, units.feet_to_meters(ftmsl)])

        lat, lon, ftmsl = end
        x, y = pyproj.transform(wgs84, utm, lon, lat)
        l2 = np.array([x, y, units.feet_to_meters(ftmsl)])

        lat, lon, ftmsl = point
        x, y = pyproj.transform(wgs84, utm, lon, lat)
        p = np.array([x, y, units.feet_to_meters(ftmsl)])
    except RuntimeError:
        # pyproj throws RuntimeError if the coordinates are grossly beyond the
        # bounds of the projection. We simplify this to "infinite" distance.
        return float("inf")

    d1 = l1 - p
    d2 = l2 - l1
    num = np.dot(d1, d2)
    dem = np.linalg.norm(l2 - l1)**2
    t = -num / dem

    if t < 0:
        t = 0
    elif t > 1:
        t = 1

    p_c = l1 + t * (l2 - l1)

    dist = np.linalg.norm(p - p_c)

    return units.meters_to_feet(dist)
