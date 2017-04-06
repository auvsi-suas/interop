"""Tests for the uas_telemetry module."""

import iso8601
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from simplekml import Kml

from auvsi_suas.models import units
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.proto.mission_pb2 import WaypointEvaluation


class TestUasTelemetryBase(TestCase):
    """Base for the UasTelemetry tests."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()

    def create_log_element(self, timestamp, user, lat, lon, alt, heading):
        pos = GpsPosition(latitude=lat, longitude=lon)
        pos.save()
        apos = AerialPosition(gps_position=pos, altitude_msl=alt)
        apos.save()
        log = UasTelemetry(timestamp=timezone.now(),
                           user=user,
                           uas_position=apos,
                           uas_heading=heading)
        log.save()
        return log


class TestUasTelemetry(TestUasTelemetryBase):
    """Tests the UasTelemetry model."""

    def setUp(self):
        super(TestUasTelemetry, self).setUp()

        self.log = self.create_log_element(timestamp=timezone.now(),
                                           user=self.user,
                                           lat=10,
                                           lon=100,
                                           alt=200,
                                           heading=90)

    def test_unicode(self):
        """Tests the unicode method executes."""
        self.assertTrue(self.log.__unicode__())

    def test_duplicate_unequal(self):
        """Tests duplicate function with unequal telemetry."""
        log1 = self.create_log_element(timestamp=timezone.now(),
                                       user=self.user,
                                       lat=20,
                                       lon=200,
                                       alt=200,
                                       heading=90)
        log2 = self.create_log_element(timestamp=timezone.now(),
                                       user=self.user,
                                       lat=10,
                                       lon=100,
                                       alt=300,
                                       heading=90)
        log3 = self.create_log_element(timestamp=timezone.now(),
                                       user=self.user,
                                       lat=10,
                                       lon=100,
                                       alt=200,
                                       heading=10)

        self.assertFalse(self.log.duplicate(log1))
        self.assertFalse(self.log.duplicate(log2))
        self.assertFalse(self.log.duplicate(log3))

    def test_duplicate_equal(self):
        """Tests duplicate function with equal telemetry."""
        log1 = self.create_log_element(timestamp=timezone.now(),
                                       user=self.user,
                                       lat=10,
                                       lon=100,
                                       alt=200,
                                       heading=90)

        self.assertTrue(self.log.duplicate(self.log))
        self.assertTrue(self.log.duplicate(log1))

    def test_json(self):
        """Tests JSON-style output."""
        data = self.log.json()

        self.assertIn('id', data)
        self.assertIn('user', data)
        self.assertIn('timestamp', data)
        self.assertIn('latitude', data)
        self.assertIn('longitude', data)
        self.assertIn('altitude_msl', data)
        self.assertIn('heading', data)

        # Timestamp is valid ISO 8601, with timezone
        iso8601.parse_date(data['timestamp'])

        self.assertEqual(10, data['latitude'])
        self.assertEqual(100, data['longitude'])
        self.assertEqual(200, data['altitude_msl'])
        self.assertEqual(90, data['heading'])


class TestUasTelemetryDedupe(TestUasTelemetryBase):
    def setUp(self):
        super(TestUasTelemetryDedupe, self).setUp()

        self.log1 = self.create_log_element(timestamp=timezone.now(),
                                            user=self.user,
                                            lat=10,
                                            lon=200,
                                            alt=200,
                                            heading=90)
        self.log2 = self.create_log_element(timestamp=timezone.now(),
                                            user=self.user,
                                            lat=20,
                                            lon=200,
                                            alt=200,
                                            heading=90)
        self.log3 = self.create_log_element(timestamp=timezone.now(),
                                            user=self.user,
                                            lat=30,
                                            lon=200,
                                            alt=200,
                                            heading=90)
        self.log4 = self.create_log_element(timestamp=timezone.now(),
                                            user=self.user,
                                            lat=40,
                                            lon=200,
                                            alt=200,
                                            heading=90)

    def test_no_logs(self):
        """Tests empty log."""
        self.assertEqual(UasTelemetry.dedupe([]), [])

    def test_no_duplicates(self):
        """Tests no duplicates in list."""
        orig = [self.log1, self.log2, self.log3, self.log4]
        self.assertEqual(UasTelemetry.dedupe(orig), orig)

    def test_boundary_duplicates(self):
        """Tests duplicates on the bounds of the list."""
        orig = [self.log1, self.log1, self.log2, self.log2, self.log2]
        expect = [self.log1, self.log2]
        self.assertEqual(UasTelemetry.dedupe(orig), expect)

    def test_duplicates(self):
        orig = [self.log1, self.log1, self.log2, self.log3, self.log3,
                self.log4, self.log4]
        expect = [self.log1, self.log2, self.log3, self.log4]
        self.assertEqual(UasTelemetry.dedupe(orig), expect)

    def create_uas_logs(self, user, entries):
        """Create a list of uas telemetry logs.

        Args:
            user: User to create logs for.
            entries: List of (lat, lon, alt) tuples for each entry.

        Returns:
            List of UasTelemetry objects
        """
        ret = []

        for (lat, lon, alt) in entries:
            pos = GpsPosition()
            pos.latitude = lat
            pos.longitude = lon
            pos.save()
            apos = AerialPosition()
            apos.altitude_msl = alt
            apos.gps_position = pos
            apos.save()
            log = UasTelemetry()
            log.user = user
            log.uas_position = apos
            log.uas_heading = 0
            log.save()
            ret.append(log)

        return ret

    def assertSatisfiedWaypoints(self, expect, got):
        """Assert two satisfied_waypoints return values are equal."""
        self.assertEqual(len(expect), len(got))
        for i in xrange(len(expect)):
            e = expect[i]
            g = got[i]
            self.assertEqual(e.id, g.id)
            self.assertAlmostEqual(e.score_ratio, g.score_ratio, places=2)
            self.assertAlmostEqual(e.closest_for_scored_approach_ft,
                                   g.closest_for_scored_approach_ft,
                                   places=2)
            self.assertAlmostEqual(e.closest_for_mission_ft,
                                   g.closest_for_mission_ft,
                                   places=2)

    def waypoints_from_data(self, waypoints_data):
        """Converts tuples of lat/lon/alt to a waypoint."""
        waypoints = []
        for i, waypoint in enumerate(waypoints_data):
            (lat, lon, alt) = waypoint
            pos = GpsPosition()
            pos.latitude = lat
            pos.longitude = lon
            pos.save()
            apos = AerialPosition()
            apos.altitude_msl = alt
            apos.gps_position = pos
            apos.save()
            wpt = Waypoint()
            wpt.position = apos
            wpt.order = i
            wpt.save()
            waypoints.append(wpt)
        return waypoints

    def test_satisfied_waypoints(self):
        """Tests the evaluation of waypoints method."""
        # Create mission config
        gpos = GpsPosition()
        gpos.latitude = 10
        gpos.longitude = 10
        gpos.save()

        # Create waypoints for testing.
        waypoints = self.waypoints_from_data([(38, -76, 100), (39, -77, 200), (
            40, -78, 0)])

        # Create UAS telemetry logs

        # Only first is valid.
        entries = [(38, -76, 140), (40, -78, 600), (37, -75, 40)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0,
                                     closest_for_mission_ft=460785.17),
                  WaypointEvaluation(id=2,
                                     score_ratio=0)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # First and last are valid, but missed second, so third doesn't count.
        entries = [(38, -76, 140), (40, -78, 600), (40, -78, 40)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0,
                                     closest_for_mission_ft=460785.03),
                  WaypointEvaluation(id=2,
                                     score_ratio=0)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Hit all.
        entries = [(38, -76, 140), (39, -77, 180), (40, -78, 40)]
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0.8,
                                     closest_for_scored_approach_ft=20,
                                     closest_for_mission_ft=20),
                  WaypointEvaluation(id=2,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40)]
        logs = self.create_uas_logs(self.user, entries)
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Only hit the first waypoint on run one, hit all on run two.
        entries = [(38, -76, 140),
                   (40, -78, 600),
                   (37, -75, 40),
                   # Run two:
                   (38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 40)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0.8,
                                     closest_for_scored_approach_ft=20,
                                     closest_for_mission_ft=20),
                  WaypointEvaluation(id=2,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Hit all on run one, only hit the first waypoint on run two.
        entries = [(38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 40),
                   # Run two:
                   (38, -76, 140),
                   (40, -78, 600),
                   (37, -75, 40)]
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0.8,
                                     closest_for_scored_approach_ft=20,
                                     closest_for_mission_ft=20),
                  WaypointEvaluation(id=2,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40)]
        logs = self.create_uas_logs(self.user, entries)
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Keep flying after hitting all waypoints.
        entries = [(38, -76, 140), (39, -77, 180), (40, -78, 40),
                   (30.1, -78.1, 100)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40),
                  WaypointEvaluation(id=1,
                                     score_ratio=0.8,
                                     closest_for_scored_approach_ft=20,
                                     closest_for_mission_ft=20),
                  WaypointEvaluation(id=2,
                                     score_ratio=0.6,
                                     closest_for_scored_approach_ft=40,
                                     closest_for_mission_ft=40)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Hit all in first run, but second is higher scoring.
        entries = [(38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 60),
                   # Run two:
                   (38, -76, 100),
                   (39, -77, 200),
                   (40, -78, 110)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=1,
                                     closest_for_scored_approach_ft=0,
                                     closest_for_mission_ft=0),
                  WaypointEvaluation(id=1,
                                     score_ratio=1,
                                     closest_for_scored_approach_ft=0,
                                     closest_for_mission_ft=0),
                  WaypointEvaluation(id=2,
                                     score_ratio=0,
                                     closest_for_mission_ft=60)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))

        # Restart waypoint path in the middle.
        waypoints = self.waypoints_from_data([(38, -76, 100), (39, -77, 200), (
            40, -78, 0)])
        entries = [(38, -76, 140),
                   (39, -77, 180),
                   # Restart:
                   (38, -76, 70),
                   (39, -77, 150),
                   (40, -78, 10)]
        logs = self.create_uas_logs(self.user, entries)
        expect = [WaypointEvaluation(id=0,
                                     score_ratio=0.7,
                                     closest_for_scored_approach_ft=30,
                                     closest_for_mission_ft=30),
                  WaypointEvaluation(id=1,
                                     score_ratio=0.5,
                                     closest_for_scored_approach_ft=50,
                                     closest_for_mission_ft=20),
                  WaypointEvaluation(id=2,
                                     score_ratio=0.9,
                                     closest_for_scored_approach_ft=10,
                                     closest_for_mission_ft=10)]
        self.assertSatisfiedWaypoints(expect, UasTelemetry.satisfied_waypoints(
            gpos, waypoints, logs))


class TestUasTelemetryKML(TestUasTelemetryBase):
    # String formatter for KML format that expects lon, lat, alt arguments
    coord_format = '<gx:coord>{} {} {}</gx:coord>'

    def create_log_element(self, lat, lon, alt):
        """Override to define defaults."""
        super(TestUasTelemetryKML, self).create_log_element(
            timestamp=timezone.now(),
            user=self.user,
            lat=lat,
            lon=lon,
            alt=alt,
            heading=80)

    def test_kml_simple(self):
        coordinates = [
            (-76.0, 38.0, 0.0),
            (-76.0, 38.0, 10.0),
            (-76.0, 38.0, 20.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 100.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 60.0),
        ]
        # Create Coordinates
        start = TakeoffOrLandingEvent(user=self.user, uas_in_air=True)
        start.save()
        for coord in coordinates:
            self.create_log_element(*coord)
        end = TakeoffOrLandingEvent(user=self.user, uas_in_air=False)
        end.save()

        kml = Kml()
        UasTelemetry.kml(user=self.user,
                         logs=UasTelemetry.by_user(self.user),
                         kml=kml,
                         kml_doc=kml)
        for coord in coordinates:
            tag = self.coord_format.format(coord[1], coord[0],
                                           units.feet_to_meters(coord[2]))
            self.assertTrue(tag in kml.kml())

    def test_kml_empty(self):
        kml = Kml()
        UasTelemetry.kml(user=self.user,
                         logs=UasTelemetry.by_user(self.user),
                         kml=kml,
                         kml_doc=kml)

    def test_kml_filter(self):
        coordinates = [
            (-76.0, 38.0, 0.0),
            (-76.0, 38.0, 10.0),
            (-76.0, 38.0, 20.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 100.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 60.0),
        ]
        filtered_out = [(0.1, 0.001, 100), (0.0, 0.0, 0)]
        # Create Coordinates
        start = TakeoffOrLandingEvent(user=self.user, uas_in_air=True)
        start.save()
        for coord in coordinates:
            self.create_log_element(*coord)
        for coord in filtered_out:
            self.create_log_element(*coord)
        end = TakeoffOrLandingEvent(user=self.user, uas_in_air=False)
        end.save()

        kml = Kml()
        UasTelemetry.kml(user=self.user,
                         logs=UasTelemetry.by_user(self.user),
                         kml=kml,
                         kml_doc=kml)

        for filtered in filtered_out:
            tag = self.coord_format.format(filtered[1], filtered[0],
                                           units.feet_to_meters(filtered[2]))
            self.assertTrue(tag not in kml.kml())

        for coord in coordinates:
            tag = self.coord_format.format(coord[1], coord[0],
                                           units.feet_to_meters(coord[2]))
            self.assertTrue(tag in kml.kml())
