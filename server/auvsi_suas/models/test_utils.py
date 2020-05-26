"""Testing utilities."""

import collections
import datetime
import functools
import json
import logging
import random
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.mission_judge_feedback import MissionJudgeFeedback
from auvsi_suas.models.odlc import Odlc
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.proto import interop_admin_api_pb2
from auvsi_suas.proto import interop_api_pb2
from django.test import Client
from django.urls import reverse
from google.protobuf import json_format

logger = logging.getLogger(__name__)

odlcs_review_url = reverse('auvsi_suas:odlcs_review')
odlcs_review_id_url = functools.partial(reverse, 'auvsi_suas:odlcs_review_id')
odlcs_url = reverse('auvsi_suas:odlcs')
telemetry_url = reverse('auvsi_suas:telemetry')


def create_sample_mission(superuser):
    """Creates a sample mission.

    Args:
        superuser: A superuser account to create mission under.
    Returns:
        MissionConfig for the created mission.
    """
    mission = MissionConfig()

    gpos = GpsPosition(latitude=38.145103, longitude=-76.427856)
    gpos.save()
    mission.home_pos = gpos

    gpos = GpsPosition(latitude=38.144778, longitude=-76.429417)
    gpos.save()
    mission.lost_comms_pos = gpos

    gpos = GpsPosition(latitude=38.145111, longitude=-76.427861)
    gpos.save()
    mission.emergent_last_known_pos = gpos

    gpos = GpsPosition(latitude=38.146747, longitude=-76.422131)
    gpos.save()
    mission.off_axis_odlc_pos = gpos

    gpos = GpsPosition(latitude=38.144680, longitude=-76.428022)
    gpos.save()
    mission.map_center_pos = gpos
    mission.map_height_ft = 1200

    gpos = GpsPosition(latitude=38.145848, longitude=-76.426374)
    gpos.save()
    mission.air_drop_pos = gpos

    gpos = GpsPosition(latitude=38.146152, longitude=-76.426396)
    gpos.save()
    mission.ugv_drive_pos = gpos

    # All foreign keys must be defined before the first save.
    # All many-to-many must be defined after the first save.
    mission.save()

    bounds = FlyZone(altitude_msl_min=100, altitude_msl_max=750)
    bounds.save()
    # yapf: disable
    pts = [(38.1462694444444, -76.4281638888889),
           (38.1516250000000, -76.4286833333333),
           (38.1518888888889, -76.4314666666667),
           (38.1505944444444, -76.4353611111111),
           (38.1475666666667, -76.4323416666667),
           (38.1446666666667, -76.4329472222222),
           (38.1432555555556, -76.4347666666667),
           (38.1404638888889, -76.4326361111111),
           (38.1407194444444, -76.4260138888889),
           (38.1437611111111, -76.4212055555556),
           (38.1473472222222, -76.4232111111111),
           (38.1461305555556, -76.4266527777778)]
    # yapf: enable
    for ix, (lat, lon) in enumerate(pts):
        wpt = Waypoint(latitude=lat,
                       longitude=lon,
                       altitude_msl=0,
                       order=ix + 1)
        wpt.save()
        bounds.boundary_pts.add(wpt)
    bounds.save()
    mission.fly_zones.add(bounds)

    # yapf: disable
    pts = [(38.146689, -76.426475, 150, 750),
           (38.142914, -76.430297, 300, 300),
           (38.149504, -76.433110, 100, 750),
           (38.148711, -76.429061, 300, 750),
           (38.144203, -76.426155,  50, 400),
           (38.146003, -76.430733, 225, 500)]
    # yapf: enable
    for lat, lon, radius, height in pts:
        obst = StationaryObstacle(latitude=lat,
                                  longitude=lon,
                                  cylinder_radius=radius,
                                  cylinder_height=height)
        obst.save()
        mission.stationary_obstacles.add(obst)

    # yapf: disable
    pts = [(38.1446916666667, -76.4279944444445, 200),
           (38.1461944444444, -76.4237138888889, 300),
           (38.1438972222222, -76.4225500000000, 400),
           (38.1417722222222, -76.4251083333333, 400),
           (38.1453500000000, -76.4286750000000, 300),
           (38.1508972222222, -76.4292972222222, 300),
           (38.1514944444444, -76.4313833333333, 300),
           (38.1505333333333, -76.4341750000000, 300),
           (38.1479472222222, -76.4316055555556, 200),
           (38.1443333333333, -76.4322888888889, 200),
           (38.1433166666667, -76.4337111111111, 300),
           (38.1410944444444, -76.4321555555556, 400),
           (38.1415777777778, -76.4252472222222, 400),
           (38.1446083333333, -76.4282527777778, 200)]
    # yapf: enable
    for ix, (lat, lon, alt) in enumerate(pts):
        wpt = Waypoint(latitude=lat,
                       longitude=lon,
                       altitude_msl=alt,
                       order=ix + 1)
        wpt.save()
        mission.mission_waypoints.add(wpt)

    # yapf: disable
    pts = [(38.1444444444444, -76.4280916666667),
           (38.1459444444444, -76.4237944444445),
           (38.1439305555556, -76.4227444444444),
           (38.1417138888889, -76.4253805555556),
           (38.1412111111111, -76.4322361111111),
           (38.1431055555556, -76.4335972222222),
           (38.1441805555556, -76.4320111111111),
           (38.1452611111111, -76.4289194444444),
           (38.1444444444444, -76.4280916666667)]
    # yapf: enable
    for ix, (lat, lon) in enumerate(pts):
        wpt = Waypoint(latitude=lat,
                       longitude=lon,
                       altitude_msl=0,
                       order=ix + 1)
        wpt.save()
        mission.search_grid_points.add(wpt)

    # yapf: disable
    pts = [(38.14616666666666, -76.42666666666668),
           (38.14636111111111, -76.42616666666667),
           (38.14558333333334, -76.42608333333334),
           (38.14541666666667, -76.42661111111111)]
    # yapf: enable
    for ix, (lat, lon) in enumerate(pts):
        wpt = Waypoint(latitude=lat,
                       longitude=lon,
                       altitude_msl=0,
                       order=ix + 1)
        wpt.save()
        mission.air_drop_boundary_points.add(wpt)

    gpos = GpsPosition(latitude=38.143844, longitude=-76.426469)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.N,
                shape=interop_api_pb2.Odlc.STAR,
                shape_color=interop_api_pb2.Odlc.RED,
                alphanumeric='A',
                alphanumeric_color=interop_api_pb2.Odlc.WHITE)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.141872, longitude=-76.426183)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.NE,
                shape=interop_api_pb2.Odlc.CROSS,
                shape_color=interop_api_pb2.Odlc.BLUE,
                alphanumeric='I',
                alphanumeric_color=interop_api_pb2.Odlc.BLACK)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.142828, longitude=-76.427644)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.E,
                shape=interop_api_pb2.Odlc.QUARTER_CIRCLE,
                shape_color=interop_api_pb2.Odlc.YELLOW,
                alphanumeric='R',
                alphanumeric_color=interop_api_pb2.Odlc.ORANGE)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.144925, longitude=-76.425100)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.SE,
                shape=interop_api_pb2.Odlc.CIRCLE,
                shape_color=interop_api_pb2.Odlc.BROWN,
                alphanumeric='V',
                alphanumeric_color=interop_api_pb2.Odlc.RED)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.146747, longitude=-76.422131)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.S,
                shape=interop_api_pb2.Odlc.TRAPEZOID,
                shape_color=interop_api_pb2.Odlc.WHITE,
                alphanumeric='E',
                alphanumeric_color=interop_api_pb2.Odlc.GRAY)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.144097, longitude=-76.431089)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.SW,
                shape=interop_api_pb2.Odlc.SQUARE,
                shape_color=interop_api_pb2.Odlc.GREEN,
                alphanumeric='H',
                alphanumeric_color=interop_api_pb2.Odlc.BLUE)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.144878, longitude=-76.423681)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.W,
                shape=interop_api_pb2.Odlc.RECTANGLE,
                shape_color=interop_api_pb2.Odlc.PURPLE,
                alphanumeric='I',
                alphanumeric_color=interop_api_pb2.Odlc.GREEN)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.142819, longitude=-76.432375)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.NW,
                shape=interop_api_pb2.Odlc.SEMICIRCLE,
                shape_color=interop_api_pb2.Odlc.ORANGE,
                alphanumeric='C',
                alphanumeric_color=interop_api_pb2.Odlc.YELLOW)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.141639, longitude=-76.429347)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.N,
                shape=interop_api_pb2.Odlc.TRIANGLE,
                shape_color=interop_api_pb2.Odlc.BLACK,
                alphanumeric='L',
                alphanumeric_color=interop_api_pb2.Odlc.PURPLE)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.142478, longitude=-76.424967)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.STANDARD,
                location=gpos,
                orientation=interop_api_pb2.Odlc.NE,
                shape=interop_api_pb2.Odlc.PENTAGON,
                shape_color=interop_api_pb2.Odlc.GRAY,
                alphanumeric='E',
                alphanumeric_color=interop_api_pb2.Odlc.BROWN)
    odlc.save()
    mission.odlcs.add(odlc)

    gpos = GpsPosition(latitude=38.143411, longitude=-76.424489)
    gpos.save()
    odlc = Odlc(mission=mission,
                user=superuser,
                odlc_type=interop_api_pb2.Odlc.EMERGENT,
                location=gpos,
                description='Randy the backpacker.')
    odlc.save()
    mission.odlcs.add(odlc)

    mission.save()
    return mission


def simulate_telemetry(test, client, mission, hit_waypoint):
    """Simulates sending telemetry."""
    t = interop_api_pb2.Telemetry()
    if hit_waypoint:
        wpt = random.choice(mission.mission_waypoints.all())
        t.latitude = wpt.latitude
        t.longitude = wpt.longitude
        t.altitude = wpt.altitude_msl
        t.heading = random.uniform(0, 360)
    else:
        t.latitude = random.uniform(0, 90)
        t.longitude = random.uniform(0, 180)
        t.altitude = random.uniform(0, 800)
        t.heading = random.uniform(0, 360)
    r = client.post(telemetry_url,
                    data=json_format.MessageToJson(t),
                    content_type='application/json')
    test.assertEqual(r.status_code, 200, r.content)


def simulate_odlc(test, client, mission, actual):
    """Simulates sending ODLC."""
    o = interop_api_pb2.Odlc()
    o.mission = mission.pk
    if actual:
        odlc = random.choice(mission.odlcs.all())
        o.type = odlc.odlc_type
        o.latitude = odlc.location.latitude
        o.longitude = odlc.location.longitude
        if odlc.shape:
            o.orientation = odlc.orientation
            o.shape = odlc.shape
            o.shape_color = odlc.shape_color
            o.alphanumeric = odlc.alphanumeric
            o.alphanumeric_color = odlc.alphanumeric_color
            o.autonomous = random.random() < 0.1
        else:
            o.description = odlc.description
    else:
        o.type = random.choice(interop_api_pb2.Odlc.Type.values())
        o.latitude = random.uniform(0, 90)
        o.longitude = random.uniform(0, 180)
        o.orientation = random.choice(
            interop_api_pb2.Odlc.Orientation.values())
        o.shape = random.choice(interop_api_pb2.Odlc.Shape.values())
        o.shape_color = random.choice(interop_api_pb2.Odlc.Color.values())
        o.alphanumeric = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        o.alphanumeric_color = random.choice(
            interop_api_pb2.Odlc.Color.values())
        o.autonomous = random.random() < 0.1
        o.description = str(random.random())
    r = client.post(odlcs_url,
                    data=json_format.MessageToJson(o),
                    content_type='application/json')
    test.assertEqual(r.status_code, 200, r.content)


def simulate_team_mission(test, mission, superuser, user):
    """Simulates a team's mission demonstration.

    Args:
        test: The test case.
        mission: The mission to simulate for.
        superuser: The superuser for admin actions.
        user: The user for the team.
    """
    total_telem = 100
    waypoints_hit = len(mission.mission_waypoints.all())
    odlcs_correct = len(mission.odlcs.all())
    odlcs_incorrect = 1

    c = Client()
    c.force_login(user)

    # Send telemetry during flight.
    TakeoffOrLandingEvent(user=user, mission=mission, uas_in_air=True).save()
    for i in range(total_telem):
        simulate_telemetry(test,
                           client=c,
                           mission=mission,
                           hit_waypoint=i < waypoints_hit)
    TakeoffOrLandingEvent(user=user, mission=mission, uas_in_air=False).save()

    # Submit ODLCs.
    for _ in range(odlcs_correct):
        simulate_odlc(test, c, mission, actual=True)
    for _ in range(odlcs_incorrect):
        simulate_odlc(test, c, mission, actual=False)

    # Judge feedback submitted.
    feedback = MissionJudgeFeedback()
    feedback.mission = mission
    feedback.user = user
    feedback.flight_time = datetime.timedelta(seconds=1)
    feedback.post_process_time = datetime.timedelta(seconds=1)
    feedback.used_timeout = False
    feedback.min_auto_flight_time = True
    feedback.safety_pilot_takeovers = 1
    feedback.out_of_bounds = 1
    feedback.unsafe_out_of_bounds = 0
    feedback.things_fell_off_uas = 0
    feedback.crashed = False
    feedback.air_drop_accuracy = interop_admin_api_pb2.MissionJudgeFeedback.WITHIN_15_FT
    feedback.ugv_drove_to_location = True
    feedback.operational_excellence_percent = 90
    feedback.save()

    # ODLCs thumbnails reviewed.
    c = Client()
    c.force_login(superuser)
    review_data = json.loads(c.get(odlcs_review_url).content)
    for odlc_review in review_data:
        pk = int(odlc_review['odlc']['id'])
        review = interop_admin_api_pb2.OldcReview()
        review.odlc.id = pk
        review.thumbnail_approved = True
        review.description_approved = True
        r = client.put(odlc_review_id_url(args=[pk]),
                       data=json_format.MessageToJson(review),
                       content_type='application/json')
        test.assertEqual(r.status_code, 200, r.content)
