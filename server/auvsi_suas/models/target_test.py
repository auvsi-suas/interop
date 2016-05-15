"""Tests for the target module."""

import os.path
from auvsi_suas.models import GpsPosition
from auvsi_suas.models import Target
from auvsi_suas.models import TargetEvaluator
from auvsi_suas.models import TargetType
from auvsi_suas.models import Color
from auvsi_suas.models import Shape
from auvsi_suas.models import Orientation
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone


class TestTarget(TestCase):
    """Tests for the Target model."""

    def setUp(self):
        """Sets up the tests."""
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

    def test_valid(self):
        """Test creating a valid target."""
        with open(os.path.join(settings.BASE_DIR,
                               'auvsi_suas/fixtures/testdata/S.jpg')) as f:
            thumb = SimpleUploadedFile('thumb.jpg', f.read())

        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   thumbnail=thumb)
        t.save()

    def test_unicode(self):
        """Test unicode conversion."""
        with open(os.path.join(settings.BASE_DIR,
                               'auvsi_suas/fixtures/testdata/S.jpg')) as f:
            thumb = SimpleUploadedFile('thumb.jpg', f.read())

        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   thumbnail=thumb)
        t.save()

        self.assertTrue(t.__unicode__())

    def test_minimal_unicode(self):
        """Unicode with only user and target."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        self.assertTrue(t.__unicode__())

    def test_null_fields(self):
        """Only user and target type."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

    def test_creation_time(self):
        """Creation time is set on creation and doesn't change on update."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        orig = t.creation_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.save()

        self.assertEqual(orig, t.creation_time)

    def test_last_modified_time(self):
        """Last modified time is set on creation and changes every update."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        orig = t.last_modified_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.save()

        self.assertGreater(t.last_modified_time, orig)

    def test_json(self):
        """Test target JSON."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   autonomous=True)
        t.save()

        d = t.json()

        self.assertIn('id', d)
        self.assertEqual(self.user.pk, d['user'])
        self.assertEqual('standard', d['type'])
        self.assertEqual(38, d['latitude'])
        self.assertEqual(-76, d['longitude'])
        self.assertEqual('s', d['orientation'])
        self.assertEqual('square', d['shape'])
        self.assertEqual('white', d['background_color'])
        self.assertEqual('ABC', d['alphanumeric'])
        self.assertEqual('black', d['alphanumeric_color'])
        self.assertEqual('Test target', d['description'])
        self.assertEqual(True, d['autonomous'])
        self.assertNotIn('thumbnail_approved', d)

        d = t.json(is_superuser=True)
        self.assertIn('thumbnail_approved', d)

        t.thumbnail_approved = True
        t.save()
        d = t.json(is_superuser=True)
        self.assertEqual(None, d['thumbnail'])
        self.assertEqual(True, d['thumbnail_approved'])

    def test_minimal_json(self):
        """Test target JSON with minimal data."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        d = t.json()

        self.assertIn('id', d)
        self.assertEqual(self.user.pk, d['user'])
        self.assertEqual('standard', d['type'])
        self.assertEqual(None, d['latitude'])
        self.assertEqual(None, d['longitude'])
        self.assertEqual(None, d['orientation'])
        self.assertEqual(None, d['shape'])
        self.assertEqual(None, d['background_color'])
        self.assertEqual(None, d['alphanumeric'])
        self.assertEqual(None, d['alphanumeric_color'])
        self.assertEqual(None, d['description'])
        self.assertEqual(False, d['autonomous'])

    def test_similar_classifications(self):
        """Tests similar classification counts are computed correctly."""
        # Test equal standard targets.
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()
        t1 = Target(user=self.user,
                    target_type=TargetType.standard,
                    location=l,
                    orientation=Orientation.s,
                    shape=Shape.square,
                    background_color=Color.white,
                    alphanumeric='ABC',
                    alphanumeric_color=Color.black,
                    description='Test target',
                    autonomous=True)
        t1.save()
        t2 = Target(user=self.user,
                    target_type=TargetType.standard,
                    location=l,
                    orientation=Orientation.s,
                    shape=Shape.square,
                    background_color=Color.white,
                    alphanumeric='ABC',
                    alphanumeric_color=Color.black,
                    description='Test other target',
                    autonomous=True)
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications(t2))

        # Test unequal standard targets.
        t1.alphanumeric = 'DEF'
        t1.alphanumeric_color = Color.blue
        t1.save()
        self.assertAlmostEqual(3.0 / 5.0, t1.similar_classifications(t2))
        t1.shape = Shape.circle
        t1.background_color = Color.orange
        t1.save()
        self.assertAlmostEqual(1.0 / 5.0, t1.similar_classifications(t2))

        # Test different types.
        t1.target_type = TargetType.off_axis
        t1.save()
        self.assertAlmostEqual(0, t1.similar_classifications(t2))

        # Test off_axis is same as standard.
        t2.target_type = TargetType.off_axis
        t2.alphanumeric = 'DEF'
        t2.save()
        self.assertAlmostEqual(2.0 / 5.0, t1.similar_classifications(t2))

        # Test emergent type is always 1.
        t1.target_type = TargetType.emergent
        t1.save()
        t2.target_type = TargetType.emergent
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications(t2))

        # Test QRC is only description.
        t1.target_type = TargetType.qrc
        t1.save()
        t2.target_type = TargetType.qrc
        t2.save()
        self.assertAlmostEqual(0.0, t1.similar_classifications(t2))
        t2.description = 'Test target'
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications(t2))


class TestTargetEvaluator(TestCase):
    """Tests for the TargetEvaluator."""

    def setUp(self):
        """Setup the test case."""
        super(TestTargetEvaluator, self).setUp()
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

        l1 = GpsPosition(latitude=38, longitude=-76)
        l1.save()
        l2 = GpsPosition(latitude=38.0003, longitude=-76)
        l2.save()
        l3 = GpsPosition(latitude=-38, longitude=76)
        l3.save()

        # A target worth full points.
        self.submit1 = Target(user=self.user,
                              target_type=TargetType.standard,
                              location=l1,
                              orientation=Orientation.s,
                              shape=Shape.square,
                              background_color=Color.white,
                              alphanumeric='ABC',
                              alphanumeric_color=Color.black,
                              description='Test target 1',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit1.save()
        self.real1 = Target(user=self.user,
                            target_type=TargetType.standard,
                            location=l1,
                            orientation=Orientation.s,
                            shape=Shape.square,
                            background_color=Color.white,
                            alphanumeric='ABC',
                            alphanumeric_color=Color.black,
                            description='Test target 1')
        self.real1.save()

        # A target worth less than full points.
        self.submit2 = Target(user=self.user,
                              target_type=TargetType.standard,
                              location=l1,
                              orientation=Orientation.n,
                              shape=Shape.circle,
                              background_color=Color.white,
                              alphanumeric='ABC',
                              alphanumeric_color=Color.black,
                              description='Test target 2',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit2.save()
        self.real2 = Target(user=self.user,
                            target_type=TargetType.standard,
                            location=l2,
                            orientation=Orientation.s,
                            shape=Shape.triangle,
                            background_color=Color.white,
                            alphanumeric='ABC',
                            alphanumeric_color=Color.black,
                            description='Test target 2')
        self.real2.save()

        # A target worth no common traits, so unmatched.
        self.submit3 = Target(user=self.user,
                              target_type=TargetType.qrc,
                              location=l1,
                              description='Incorrect description',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit3.save()
        self.real3 = Target(user=self.user,
                            target_type=TargetType.qrc,
                            location=l3,
                            description='Test target 3')
        self.real3.save()

        # Unapproved image worth no points, so unmatched.
        self.submit4 = Target(user=self.user,
                              target_type=TargetType.qrc,
                              location=l1,
                              description='Test target 4',
                              autonomous=False,
                              thumbnail_approved=False)
        self.submit4.save()
        self.real4 = Target(user=self.user,
                            target_type=TargetType.qrc,
                            location=l1,
                            description='Test target 4')
        self.real4.save()

        self.submitted_targets = [self.submit1, self.submit2, self.submit3,
                                  self.submit4]
        self.real_targets = [self.real3, self.real1, self.real4, self.real2]
        self.real_matched_targets = [self.real1, self.real2]

    def test_match_value(self):
        """Tests the match value for two targets."""
        e = TargetEvaluator([], [])
        self.assertEqual(6, e.match_value(self.submit1, self.real1))
        self.assertEqual(3, e.match_value(self.submit2, self.real2))
        self.assertEqual(0, e.match_value(self.submit3, self.real3))
        self.assertEqual(0, e.match_value(self.submit4, self.real4))

    def test_match_targets_no_eligible(self):
        """Tests matching with no eligible matches."""
        e = TargetEvaluator([], [])
        self.assertEqual({}, e.match_targets([], []))
        self.assertEqual({}, e.match_targets(self.submitted_targets, []))
        self.assertEqual({}, e.match_targets([], self.real_targets))
        self.assertEqual({}, e.match_targets([self.submit1], [self.real4]))

    def test_match_targets(self):
        """Tests that matching targets produce maximal matches."""
        e = TargetEvaluator([], [])
        self.assertEqual(
            {
                self.submit1: self.real1,
                self.submit2: self.real2,
                self.real1: self.submit1,
                self.real2: self.submit2
            }, e.match_targets(self.submitted_targets, self.real_targets))

    def test_evaluation_dict(self):
        """Tests that the evaluation dictionary is generated correctly."""
        e = TargetEvaluator(self.submitted_targets, self.real_targets)
        d = e.evaluation_dict()

        self.assertIn('matched_target_value', d)
        self.assertIn('unmatched_target_count', d)
        self.assertIn('targets', d)
        for t in d['targets'].values():
            keys = ['match_value', 'image_approved', 'classifications',
                    'location_accuracy']
            for key in keys:
                self.assertIn(key, t)
        for s in self.real_targets:
            if s in self.real_matched_targets:
                self.assertIn(s.pk, d['targets'].keys())
            else:
                self.assertNotIn(s.pk, d['targets'].keys())

        self.assertEqual(9, d['matched_target_value'])
        self.assertEqual(2, d['unmatched_target_count'])
        self.assertEqual(6, d['targets'][self.real1.pk]['match_value'])
        self.assertEqual(True, d['targets'][self.real1.pk]['image_approved'])
        self.assertEqual(1.0, d['targets'][self.real1.pk]['classifications'])
        self.assertEqual(0.0, d['targets'][self.real1.pk]['location_accuracy'])
