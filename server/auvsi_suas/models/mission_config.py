"""Mission configuration model."""

import datetime
import itertools
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from auvsi_suas.models import units
from auvsi_suas.patches.simplekml_patch import Color
from auvsi_suas.patches.simplekml_patch import AltitudeMode
from fly_zone import FlyZone
from gps_position import GpsPosition
from mission_clock_event import MissionClockEvent
from moving_obstacle import MovingObstacle
from stationary_obstacle import StationaryObstacle
from takeoff_or_landing_event import TakeoffOrLandingEvent
from target import Target
from target import TargetEvaluator
from time_period import TimePeriod
from uas_telemetry import UasTelemetry
from waypoint import Waypoint

# Logging for the module
logger = logging.getLogger(__name__)


class MissionConfig(models.Model):
    """The details for the mission.

    Attributes:
        is_active: Whether the mission is active. Only one mission can be
            active at a time.
        home_pos: The home position for use as a reference point. Should be the
            tents.
        fly_zones: Valid areas for the UAS to fly.
        mission_waypoints: The waypoints that define the mission waypoint path
        search_grid_points: The polygon that defines the search grid.
        targets: The judge created targets.
        emergent_last_known_pos: The last known position of the emergent target.
        off_axis_target_pos: Off-axis target position.
        air_drop_pos: The air drop position.
        stationary_obstacles: The stationary obstacles.
        moving_obstacles: The moving obstacles.
    """
    is_active = models.BooleanField(default=False)
    home_pos = models.ForeignKey(GpsPosition,
                                 related_name="missionconfig_home_pos")
    fly_zones = models.ManyToManyField(FlyZone)
    mission_waypoints = models.ManyToManyField(
        Waypoint,
        related_name='missionconfig_mission_waypoints')
    search_grid_points = models.ManyToManyField(
        Waypoint,
        related_name='missionconfig_search_grid_points')
    targets = models.ManyToManyField(Target,
                                     related_name='missionconfig_targets')
    emergent_last_known_pos = models.ForeignKey(
        GpsPosition,
        related_name='missionconfig_emergent_last_known_pos')
    off_axis_target_pos = models.ForeignKey(
        GpsPosition,
        related_name='missionconfig_off_axis_target_pos')
    air_drop_pos = models.ForeignKey(GpsPosition,
                                     related_name='missionconfig_air_drop_pos')
    stationary_obstacles = models.ManyToManyField(StationaryObstacle)
    moving_obstacles = models.ManyToManyField(MovingObstacle)

    def __unicode__(self):
        """Descriptive text for use in displays."""
        mission_waypoints = ['%s' % wpt.__unicode__()
                             for wpt in self.mission_waypoints.all()]

        search_grid = ['%s' % wpt.__unicode__()
                       for wpt in self.search_grid_points.all()]

        stationary_obstacles = ['%s' % obst.__unicode__()
                                for obst in self.stationary_obstacles.all()]

        moving_obstacles = ['%s' % obst.__unicode__()
                            for obst in self.moving_obstacles.all()]

        return unicode(
            'MissionConfig (pk:%s, is_active: %s, home_pos:%s, '
            'mission_waypoints:%s, search_grid:%s, '
            'emergent_lkp:%s, off_axis:%s, '
            'air_drop_pos:%s, stationary_obstacles:%s, moving_obstacles:%s)' %
            (str(self.pk), str(self.is_active), self.home_pos.__unicode__(),
             mission_waypoints, search_grid,
             self.emergent_last_known_pos.__unicode__(),
             self.off_axis_target_pos.__unicode__(),
             self.air_drop_pos.__unicode__(), stationary_obstacles,
             moving_obstacles))

    def json(self, is_superuser):
        """Return a dict, for conversion to JSON."""
        ret = {
            'id': self.pk,
            'active': self.is_active,
            'home_pos': {
                'latitude': self.home_pos.latitude,
                'longitude': self.home_pos.longitude,
            },
            "fly_zones": [],  # Filled in below
            "mission_waypoints": [],  # Filled in below
            "search_grid_points": [],  # Filled in below
            'off_axis_target_pos': {
                'latitude': self.off_axis_target_pos.latitude,
                'longitude': self.off_axis_target_pos.longitude,
            },
            "emergent_last_known_pos": {
                "latitude": self.emergent_last_known_pos.latitude,
                "longitude": self.emergent_last_known_pos.longitude,
            },
            'air_drop_pos': {
                'latitude': self.air_drop_pos.latitude,
                'longitude': self.air_drop_pos.longitude,
            },
        }
        for zone in self.fly_zones.all():
            pts = [
                {
                    "latitude": bpt.position.gps_position.latitude,
                    "longitude": bpt.position.gps_position.longitude,
                    "order": bpt.order
                } for bpt in zone.boundary_pts.order_by('order')
            ]
            ret['fly_zones'].append({
                "boundary_pts": pts,
                "altitude_msl_min": zone.altitude_msl_min,
                "altitude_msl_max": zone.altitude_msl_max
            })
        for waypoint in self.mission_waypoints.all():
            ret['mission_waypoints'].append({
                'order': waypoint.order,
                'latitude': waypoint.position.gps_position.latitude,
                'longitude': waypoint.position.gps_position.longitude,
                'altitude_msl': waypoint.position.altitude_msl,
            })
        for point in self.search_grid_points.all():
            ret['search_grid_points'].append({
                'order': point.order,
                'latitude': point.position.gps_position.latitude,
                'longitude': point.position.gps_position.longitude,
                'altitude_msl': point.position.altitude_msl,
            })
        if not is_superuser:
            return ret

        ret.update({
            'stationary_obstacles': [],  # Filled in below
            'moving_obstacles': [],  # Filled in below
        })
        for obst in self.stationary_obstacles.all():
            ret['stationary_obstacles'].append({
                'latitude': obst.gps_position.latitude,
                'longitude': obst.gps_position.longitude,
                'cylinder_radius': obst.cylinder_radius,
                'cylinder_height': obst.cylinder_height,
            })
        for obst in self.moving_obstacles.all():
            ret['moving_obstacles'].append({
                'speed_avg': obst.speed_avg,
                'sphere_radius': obst.sphere_radius,
            })
        return ret

    @classmethod
    def kml_all(cls, kml, missions=None):
        """
        Appends kml nodes describing all mission configurations.

        Args:
            kml: A simpleKML Container to which the mission data will be added
            missions: Optional list of mission for which to generate KML. If
                None, it will use all missions.
        """
        if not missions:
            missions = MissionConfig.objects.all()

        for mission in missions:
            mission.kml(kml)

    def kml(self, kml):
        """
        Appends kml nodes describing this mission configurations.

        Args:
            kml: A simpleKML Container to which the mission data will be added
        """
        mission_name = 'Mission {}'.format(self.pk)
        kml_folder = kml.newfolder(name=mission_name)

        # Static Points
        locations = {
            'Home Position': self.home_pos,
            'Emergent LKP': self.emergent_last_known_pos,
            'Off Axis': self.off_axis_target_pos,
            'Air Drop': self.air_drop_pos,
        }
        for key, point in locations.iteritems():
            gps = (point.longitude, point.latitude)
            wp = kml_folder.newpoint(name=key, coords=[gps])
            wp.description = str(point)

        # Waypoints
        waypoints_folder = kml_folder.newfolder(name='Waypoints')
        linestring = waypoints_folder.newlinestring(name='Waypoints')
        waypoints = []
        waypoint_num = 1
        for waypoint in self.mission_waypoints.all():
            gps = waypoint.position.gps_position
            coord = (gps.longitude, gps.latitude,
                     units.feet_to_meters(waypoint.position.altitude_msl))
            waypoints.append(coord)

            # Add waypoint marker
            wp = waypoints_folder.newpoint(name=str(waypoint_num),
                                           coords=[coord])
            wp.description = str(waypoint)
            wp.altitudemode = AltitudeMode.absolute
            wp.extrude = 1
            wp.visibility = False
            waypoint_num += 1
        linestring.coords = waypoints

        # Waypoints Style
        linestring.altitudemode = AltitudeMode.absolute
        linestring.extrude = 1
        linestring.style.linestyle.color = Color.black
        linestring.style.polystyle.color = Color.changealphaint(100,
                                                                Color.green)

        # Search Area
        search_area_folder = kml_folder.newfolder(name='Search Area')
        search_area = []
        search_area_num = 1
        for point in self.search_grid_points.all():
            gps = point.position.gps_position
            coord = (gps.longitude, gps.latitude,
                     units.feet_to_meters(point.position.altitude_msl))
            search_area.append(coord)

            # Add boundary marker
            wp = search_area_folder.newpoint(name=str(search_area_num),
                                             coords=[coord])
            wp.description = str(point)
            wp.visibility = False
            search_area_num += 1
        if search_area:
            # Create search area polygon.
            pol = search_area_folder.newpolygon(name='Search Area')
            search_area.append(search_area[0])
            pol.outerboundaryis = search_area
            # Search Area Style.
            pol.style.linestyle.color = Color.black
            pol.style.linestyle.width = 2
            pol.style.polystyle.color = Color.changealphaint(50, Color.blue)

        # Stationary Obstacles
        stationary_obstacles_folder = kml_folder.newfolder(
            name='Stationary Obstacles')
