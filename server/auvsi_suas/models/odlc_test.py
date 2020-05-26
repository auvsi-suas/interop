"""Tests for the odlc module."""

import os.path
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.odlc import Odlc
from auvsi_suas.models.odlc import OdlcEvaluator
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.proto import interop_api_pb2
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase


class TestOdlc(TestCase):
    """Tests for the Odlc model."""
    def setUp(self):
        """Sets up the tests."""
        super(TestOdlc, self).setUp()
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

        # Mission
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        wpt = Waypoint()
        wpt.latitude = 10
        wpt.longitude = 100
        wpt.altitude_msl = 1000
        wpt.order = 10
        wpt.save()
        self.mission = MissionConfig()
        self.mission.home_pos = pos
        self.mission.lost_comms_pos = pos
        self.mission.emergent_last_known_pos = pos
        self.mission.off_axis_odlc_pos = pos
        self.mission.map_center_pos = pos
        self.mission.map_height_ft = 1
        self.mission.air_drop_pos = pos
        self.mission.ugv_drive_pos = pos
        self.mission.save()
        self.mission.mission_waypoints.add(wpt)
        self.mission.search_grid_points.add(wpt)
        self.mission.save()

    def test_valid(self):
        """Test creating a valid odlc."""
        with open(os.path.join(settings.BASE_DIR, 'auvsi_suas/testdata/S.jpg'),
                  'rb') as f:
            thumb = SimpleUploadedFile('thumb.jpg', f.read())

        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD,
                 location=l,
                 orientation=interop_api_pb2.Odlc.S,
                 shape=interop_api_pb2.Odlc.SQUARE,
                 shape_color=interop_api_pb2.Odlc.WHITE,
                 alphanumeric='ABC',
                 alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                 description='Test odlc',
                 thumbnail=thumb)
        t.save()

    def test_null_fields(self):
        """Only user and odlc type."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

    def test_creation_time(self):
        """Creation time is set on creation and doesn't change on update."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        orig = t.creation_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.save()

        self.assertEqual(orig, t.creation_time)

    def test_last_modified_time(self):
        """Last modified time is set on creation and changes every update."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        orig = t.last_modified_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.update_last_modified()
        t.save()

        self.assertGreater(t.last_modified_time, orig)

    def test_similar_orientation(self):
        """Test similar orientations are computed correctly."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()
        t1 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD,
                  location=l,
                  orientation=interop_api_pb2.Odlc.S,
                  shape=interop_api_pb2.Odlc.SQUARE,
                  shape_color=interop_api_pb2.Odlc.WHITE,
                  alphanumeric='ABC',
                  alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                  description='Test odlc',
                  description_approved=True,
                  autonomous=True)
        t1.save()
        t2 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD,
                  location=l,
                  orientation=interop_api_pb2.Odlc.S,
                  shape=interop_api_pb2.Odlc.SQUARE,
                  shape_color=interop_api_pb2.Odlc.WHITE,
                  alphanumeric='ABC',
                  alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                  description='Test other odlc',
                  description_approved=False,
                  autonomous=True)
        t2.save()

        # Requires exact same orientation.
        for alpha in ['A', 'a']:
            t1.alphanumeric = alpha
            t1.orientation = interop_api_pb2.Odlc.S
            t2.orientation = interop_api_pb2.Odlc.S
            self.assertTrue(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.N
            self.assertFalse(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.E
            self.assertFalse(t1.similar_orientation(t2))

        # Accepts rotation.
        for alpha in ['I', 'H', '8']:
            t1.alphanumeric = alpha
            t1.orientation = interop_api_pb2.Odlc.S
            t2.orientation = interop_api_pb2.Odlc.S
            self.assertTrue(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.N
            self.assertTrue(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.E
            self.assertFalse(t1.similar_orientation(t2))

        # Accepts any.
        for alpha in ['O', 'o', '0']:
            t1.alphanumeric = alpha
            t1.orientation = interop_api_pb2.Odlc.S
            t2.orientation = interop_api_pb2.Odlc.S
            self.assertTrue(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.N
            self.assertTrue(t1.similar_orientation(t2))
            t2.orientation = interop_api_pb2.Odlc.E
            self.assertTrue(t1.similar_orientation(t2))

    def test_similar_classifications_ratio(self):
        """Tests similar classification ratios are computed correctly."""
        # Test equal standard odlcs.
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()
        t1 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD,
                  location=l,
                  orientation=interop_api_pb2.Odlc.S,
                  shape=interop_api_pb2.Odlc.SQUARE,
                  shape_color=interop_api_pb2.Odlc.WHITE,
                  alphanumeric='ABC',
                  alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                  description='Test odlc',
                  description_approved=True,
                  autonomous=True)
        t1.save()
        t2 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD,
                  location=l,
                  orientation=interop_api_pb2.Odlc.S,
                  shape=interop_api_pb2.Odlc.SQUARE,
                  shape_color=interop_api_pb2.Odlc.WHITE,
                  alphanumeric='ABC',
                  alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                  description='Test other odlc',
                  description_approved=False,
                  autonomous=True)
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications_ratio(t2))

        # Test unequal standard odlcs.
        t1.alphanumeric = 'DEF'
        t1.alphanumeric_color = interop_api_pb2.Odlc.BLUE
        t1.save()
        self.assertAlmostEqual(3.0 / 5.0, t1.similar_classifications_ratio(t2))
        t1.shape = interop_api_pb2.Odlc.CIRCLE
        t1.shape_color = interop_api_pb2.Odlc.ORANGE
        t1.save()
        self.assertAlmostEqual(1.0 / 5.0, t1.similar_classifications_ratio(t2))

        # Test emergent type based on description approval.
        t1.odlc_type = interop_api_pb2.Odlc.EMERGENT
        t1.save()
        t2.odlc_type = interop_api_pb2.Odlc.EMERGENT
        t2.save()
        self.assertAlmostEqual(0.0, t1.similar_classifications_ratio(t2))
        t2.description_approved = True
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications_ratio(t2))

    def test_actionable_submission(self):
        """Tests actionable_submission correctly filters submissions."""
        # t1 created and updated before take off.
        t1 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t1.save()
        t1.alphanumeric = 'A'
        t1.update_last_modified()
        t1.save()

        # t2 created before take off and updated in flight.
        t2 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t2.save()

        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()

        t2.alphanumeric = 'A'
        t2.update_last_modified()
        t2.save()

        # t3 created and updated in flight.
        t3 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t3.save()
        t3.alphanumeric = 'A'
        t3.update_last_modified()
        t3.save()

        # t4 created in flight and updated after landing.
        t4 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t4.save()

        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=False)
        event.save()

        t4.alphanumeric = 'A'
        t4.update_last_modified()
        t4.save()

        # t5 created and updated after landing.
        t5 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t5.save()
        t5.alphanumeric = 'A'
        t5.update_last_modified()
        t5.save()

        # t6 created and updated in second flight.
        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()
        t6 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t6.save()
        t6.alphanumeric = 'A'
        t6.update_last_modified()
        t6.save()
        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=False)
        event.save()

        # t7 which is not actionable.
        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()
        t7 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=False)
        event.save()

        flights = TakeoffOrLandingEvent.flights(self.mission, self.user)

        self.assertFalse(t1.actionable_submission(flights))
        self.assertFalse(t2.actionable_submission(flights))
        self.assertTrue(t3.actionable_submission(flights))
        self.assertFalse(t4.actionable_submission(flights))
        self.assertFalse(t5.actionable_submission(flights))
        self.assertFalse(t6.actionable_submission(flights))
        self.assertFalse(t7.actionable_submission(flights))


class TestOdlcEvaluator(TestCase):
    """Tests for the OdlcEvaluator."""
    def setUp(self):
        """Setup the test case."""
        super(TestOdlcEvaluator, self).setUp()
        self.maxDiff = None
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

        l1 = GpsPosition(latitude=38, longitude=-76)
        l1.save()
        l2 = GpsPosition(latitude=38.0003, longitude=-76)
        l2.save()
        l3 = GpsPosition(latitude=-38, longitude=76)
        l3.save()
        l4 = GpsPosition(latitude=0, longitude=0)
        l4.save()

        # Mission
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        wpt = Waypoint()
        wpt.order = 10
        wpt.latitude = 10
        wpt.longitude = 100
        wpt.altitude_msl = 1000
        wpt.save()
        self.mission = MissionConfig()
        self.mission.home_pos = pos
        self.mission.lost_comms_pos = pos
        self.mission.emergent_last_known_pos = pos
        self.mission.off_axis_odlc_pos = pos
        self.mission.map_center_pos = pos
        self.mission.map_height_ft = 1
        self.mission.air_drop_pos = pos
        self.mission.ugv_drive_pos = pos
        self.mission.save()
        self.mission.mission_waypoints.add(wpt)
        self.mission.search_grid_points.add(wpt)
        self.mission.save()

        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=True)
        event.save()

        # A odlc worth full points.
        self.submit1 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.STANDARD,
                            location=l1,
                            orientation=interop_api_pb2.Odlc.S,
                            shape=interop_api_pb2.Odlc.SQUARE,
                            shape_color=interop_api_pb2.Odlc.WHITE,
                            alphanumeric='ABC',
                            alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                            description='Submit test odlc 1',
                            description_approved=True,
                            autonomous=True,
                            thumbnail_approved=True)
        self.submit1.save()
        self.real1 = Odlc(mission=self.mission,
                          user=self.user,
                          odlc_type=interop_api_pb2.Odlc.STANDARD,
                          location=l1,
                          orientation=interop_api_pb2.Odlc.S,
                          shape=interop_api_pb2.Odlc.SQUARE,
                          shape_color=interop_api_pb2.Odlc.WHITE,
                          alphanumeric='ABC',
                          alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                          description='Real odlc 1')
        self.real1.save()

        # A odlc worth less than full points.
        self.submit2 = Odlc(
            mission=self.mission,
            user=self.user,
            odlc_type=interop_api_pb2.Odlc.STANDARD,
            location=l1,
            orientation=interop_api_pb2.Odlc.N,
            shape=interop_api_pb2.Odlc.CIRCLE,
            shape_color=interop_api_pb2.Odlc.WHITE,
            # alphanumeric set below
            alphanumeric_color=interop_api_pb2.Odlc.BLACK,
            description='Submit test odlc 2',
            autonomous=False,
            thumbnail_approved=True)
        self.submit2.save()
        self.real2 = Odlc(mission=self.mission,
                          user=self.user,
                          odlc_type=interop_api_pb2.Odlc.STANDARD,
                          location=l2,
                          orientation=interop_api_pb2.Odlc.S,
                          shape=interop_api_pb2.Odlc.TRIANGLE,
                          shape_color=interop_api_pb2.Odlc.WHITE,
                          alphanumeric='ABC',
                          alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                          description='Real test odlc 2')
        self.real2.save()

        # A odlc worth no points, so unmatched.
        self.submit3 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.STANDARD,
                            location=l4,
                            orientation=interop_api_pb2.Odlc.NW,
                            shape=interop_api_pb2.Odlc.PENTAGON,
                            shape_color=interop_api_pb2.Odlc.GRAY,
                            alphanumeric='XYZ',
                            alphanumeric_color=interop_api_pb2.Odlc.ORANGE,
                            description='Incorrect description',
                            autonomous=False,
                            thumbnail_approved=True)
        self.submit3.save()
        self.real3 = Odlc(
            mission=self.mission,
            user=self.user,
            odlc_type=interop_api_pb2.Odlc.STANDARD,
            orientation=interop_api_pb2.Odlc.E,
            shape=interop_api_pb2.Odlc.SEMICIRCLE,
            shape_color=interop_api_pb2.Odlc.YELLOW,
            alphanumeric='LMN',
            # alphanumeric_color set below
            location=l3,
            description='Test odlc 3')
        self.real3.save()

        # Odlcs without approved image has no match value.
        self.submit4 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.EMERGENT,
                            location=l1,
                            description='Test odlc 4',
                            autonomous=False,
                            thumbnail_approved=False)
        self.submit4.save()
        self.real4 = Odlc(mission=self.mission,
                          user=self.user,
                          odlc_type=interop_api_pb2.Odlc.EMERGENT,
                          location=l1,
                          description='Test odlc 4')
        self.real4.save()

        # A odlc without location worth fewer points.
        self.submit5 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.STANDARD,
                            orientation=interop_api_pb2.Odlc.N,
                            shape=interop_api_pb2.Odlc.TRAPEZOID,
                            shape_color=interop_api_pb2.Odlc.PURPLE,
                            alphanumeric='PQR',
                            alphanumeric_color=interop_api_pb2.Odlc.BLUE,
                            description='Test odlc 5',
                            autonomous=False,
                            thumbnail_approved=True)
        self.submit5.save()
        self.real5 = Odlc(mission=self.mission,
                          user=self.user,
                          odlc_type=interop_api_pb2.Odlc.STANDARD,
                          location=l1,
                          orientation=interop_api_pb2.Odlc.N,
                          shape=interop_api_pb2.Odlc.TRAPEZOID,
                          shape_color=interop_api_pb2.Odlc.PURPLE,
                          alphanumeric='PQR',
                          alphanumeric_color=interop_api_pb2.Odlc.BLUE,
                          description='Test odlc 5')
        self.real5.save()

        # Emergent odlc with correct description.
        self.submit6 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.EMERGENT,
                            location=l1,
                            description='Submit test odlc 6',
                            description_approved=True,
                            autonomous=True,
                            thumbnail_approved=True)
        self.submit6.save()
        self.real6 = Odlc(mission=self.mission,
                          user=self.user,
                          odlc_type=interop_api_pb2.Odlc.EMERGENT,
                          location=l1,
                          description='Real odlc 1',
                          description_approved=True)
        self.real6.save()

        event = TakeoffOrLandingEvent(user=self.user,
                                      mission=self.mission,
                                      uas_in_air=False)
        event.save()

        # submit2 updated after landing.
        self.submit2.alphanumeric = 'ABC'
        self.submit2.update_last_modified()
        self.submit2.save()
        self.submit2.update_last_modified()
        self.submit3.alphanumeric_color = interop_api_pb2.Odlc.YELLOW
        self.submit3.update_last_modified()
        self.submit3.save()
        # Unused but not unmatched odlc.
        self.submit7 = Odlc(mission=self.mission,
                            user=self.user,
                            odlc_type=interop_api_pb2.Odlc.STANDARD,
                            location=l4,
                            alphanumeric_color=interop_api_pb2.Odlc.BLACK,
                            description='Submit unused test odlc 1',
                            autonomous=False,
                            thumbnail_approved=True)
        self.submit7.save()

        self.submitted_odlcs = [
            self.submit7, self.submit6, self.submit5, self.submit4,
            self.submit3, self.submit2, self.submit1
        ]
        self.real_odlcs = [
            self.real1, self.real2, self.real3, self.real4, self.real5,
            self.real6
        ]

        self.flights = TakeoffOrLandingEvent.flights(self.mission, self.user)

    def test_match_value(self):
        """Tests the match value for two odlcs."""
        e = OdlcEvaluator(self.submitted_odlcs, self.real_odlcs, self.flights)
        self.assertAlmostEqual(1.0,
                               e.evaluate_match(self.submit1,
                                                self.real1).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.3481,
                               e.evaluate_match(self.submit2,
                                                self.real2).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.0,
                               e.evaluate_match(self.submit3,
                                                self.real3).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.0,
                               e.evaluate_match(self.submit4,
                                                self.real4).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.5,
                               e.evaluate_match(self.submit5,
                                                self.real5).score_ratio,
                               places=3)
        self.assertAlmostEqual(1.0,
                               e.evaluate_match(self.submit6,
                                                self.real6).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.08,
                               e.evaluate_match(self.submit7,
                                                self.real1).score_ratio,
                               places=3)

        self.assertAlmostEqual(0.628,
                               e.evaluate_match(self.submit1,
                                                self.real2).score_ratio,
                               places=3)
        self.assertAlmostEqual(0.64,
                               e.evaluate_match(self.submit2,
                                                self.real1).score_ratio,
                               places=3)

    def test_match_odlcs(self):
        """Tests that matching odlcs produce maximal matches."""
        e = OdlcEvaluator(self.submitted_odlcs, self.real_odlcs, self.flights)
        self.assertDictEqual(
            {
                self.submit1: self.real1,
                self.submit2: self.real2,
                self.submit5: self.real5,
                self.submit6: self.real6,
                self.real1: self.submit1,
                self.real2: self.submit2,
                self.real5: self.submit5,
                self.real6: self.submit6,
            }, e.match_odlcs(self.submitted_odlcs, self.real_odlcs))

    def test_evaluate(self):
        """Tests that the evaluation is generated correctly."""
        e = OdlcEvaluator(self.submitted_odlcs, self.real_odlcs, self.flights)
        d = e.evaluate()
        td = {t.real_odlc: t for t in d.odlcs}

        self.assertEqual(self.submit1.pk, td[self.real1.pk].submitted_odlc)
        self.assertEqual(True, td[self.real1.pk].image_approved)
        self.assertEqual(1.0, td[self.real1.pk].classifications_ratio)
        self.assertEqual(0.0, td[self.real1.pk].geolocation_accuracy_ft)
        self.assertEqual(True, td[self.real1.pk].actionable_submission)
        self.assertEqual(1.0, td[self.real1.pk].classifications_score_ratio)
        self.assertEqual(1.0, td[self.real1.pk].geolocation_score_ratio)
        self.assertEqual(1.0, td[self.real1.pk].actionable_score_ratio)
        self.assertEqual(1.0, td[self.real1.pk].autonomous_score_ratio)
        self.assertAlmostEqual(1.0, td[self.real1.pk].score_ratio)

        self.assertEqual(self.submit2.pk, td[self.real2.pk].submitted_odlc)
        self.assertEqual(True, td[self.real2.pk].image_approved)
        self.assertEqual(0.6, td[self.real2.pk].classifications_ratio)
        self.assertAlmostEqual(109.444,
                               td[self.real2.pk].geolocation_accuracy_ft,
                               places=3)
        self.assertEqual(False, td[self.real2.pk].actionable_submission)
        self.assertEqual(0.6, td[self.real2.pk].classifications_score_ratio)
        self.assertAlmostEqual(0.270,
                               td[self.real2.pk].geolocation_score_ratio,
                               places=3)
        self.assertEqual(0.0, td[self.real2.pk].actionable_score_ratio)
        self.assertAlmostEqual(0.3481, td[self.real2.pk].score_ratio, places=3)

        self.assertEqual(True, td[self.real6.pk].description_approved)
        self.assertAlmostEqual(0.375, d.score_ratio, places=3)
        self.assertEqual(2, d.unmatched_odlc_count)

    def test_evaluate_no_submitted_odlcs(self):
        """Tests that evaluation works with no submitted odlcs."""
        e = OdlcEvaluator([], self.real_odlcs, self.flights)
        d = e.evaluate()

        self.assertEqual(0, d.matched_score_ratio)
        self.assertEqual(0, d.unmatched_odlc_count)
        self.assertEqual(6, len(d.odlcs))

    def test_evaluate_no_real_odlcs(self):
        """Tests that evaluation works with no real odlcs."""
        e = OdlcEvaluator(self.submitted_odlcs, [], self.flights)
        d = e.evaluate()

        self.assertEqual(0, d.matched_score_ratio)
        self.assertEqual(7, d.unmatched_odlc_count)
        self.assertAlmostEqual(-0.35, d.score_ratio, places=3)
        self.assertEqual(0, len(d.odlcs))
