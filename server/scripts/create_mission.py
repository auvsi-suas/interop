import os
import sys

# Add server code to Python PATH for imports.
sys.path.append('/interop/server')
# Add environment variable to get Django settings file.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import json

from django.contrib.auth.models import User
from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.waypoint import Waypoint


def get_or_prompt_gpos(data, key):
    pos = data.get(key, None)
    if pos is None:
        pos = {}
        print("{} not found, please specify:".format(key))
        pos["latitude"] = input("    Latitude: ")
        pos["longitude"] = input("    Longitude: ")

    lat = pos["latitude"]
    lon = pos["longitude"]
    print("Loaded {} at {}, {}".format(key, lat, lon))

    gpos = GpsPosition(latitude=lat, longitude=lon)
    gpos.save()
    return gpos


def load_waypoint_series(series, point_data):
    for i, point in enumerate(point_data):
        wpt = Waypoint(
            latitude=point["latitude"],
            longitude=point["longitude"],
            altitude_msl=point.get("altitude", 0),
            order=i + 1)
        wpt.save()
        series.add(wpt)


def create_mission(data):
    mission = MissionConfig()
    mission.home_pos = get_or_prompt_gpos(data, "homePos")
    mission.lost_comms_pos = get_or_prompt_gpos(data, "lostCommsPos")
    mission.off_axis_odlc_pos = get_or_prompt_gpos(data, "offAxisOdlcPos")
    mission.emergent_last_known_pos = get_or_prompt_gpos(
        data, "emergentLastKnownPos")
    mission.air_drop_pos = get_or_prompt_gpos(data, "airDropPos")
    mission.ugv_drive_pos = get_or_prompt_gpos(data, "ugvDrivePos")

    mission.save()

    for flyZoneData in data.get("flyZones", []):
        print("Loading fly zone")
        bounds = FlyZone(
            altitude_msl_min=flyZoneData["altitudeMin"],
            altitude_msl_max=flyZoneData["altitudeMax"])
        bounds.save()
        load_waypoint_series(bounds.boundary_pts,
                             flyZoneData["boundaryPoints"])
        bounds.save()
        mission.fly_zones.add(bounds)

    print("Loading waypoints")
    load_waypoint_series(mission.mission_waypoints, data.get("waypoints", []))
    print("Loading search grid")
    load_waypoint_series(mission.search_grid_points,
                         data.get("searchGridPoints", []))
    print("Loading air drop boundary")
    load_waypoint_series(mission.air_drop_boundary_points,
                         data.get("airDropBoundaryPoints", []))

    for point in data.get("stationaryObstacles", []):
        obs = StationaryObstacle(
            latitude=point["latitude"],
            longitude=point["longitude"],
            cylinder_height=point["height"],
            cylinder_radius=point["radius"])
        obs.save()
        mission.stationary_obstacles.add(obs)

    mission.save()


if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser("Interop mission creation script")
    parser.add_argument("-m", "--mission", help="Mission JSON file")

    args = parser.parse_args()

    data = {}
    if args.mission is not None:
        with open(args.mission, "r") as f:
            data = json.load(f)

    create_mission(data)
