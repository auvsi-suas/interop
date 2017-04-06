"""Tests for the missions module."""

import functools
import json
import os.path
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.target import Color
from auvsi_suas.models.target import Orientation
from auvsi_suas.models.target import Shape
from auvsi_suas.models.target import Target
from auvsi_suas.models.target import TargetType
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import TestCase

login_url = reverse('auvsi_suas:login')
targets_url = reverse('auvsi_suas:targets')
targets_id_url = functools.partial(reverse, 'auvsi_suas:targets_id')
targets_id_image_url = functools.partial(reverse,
                                         'auvsi_suas:targets_id_image')
targets_review_url = reverse('auvsi_suas:targets_review')
targets_review_id_url = functools.partial(reverse,
                                          'auvsi_suas:targets_review_id')


class TestTargetsLoggedOut(TestCase):
    """Tests logged out targets."""

    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        target = {'type': 'standard', 'latitude': 38, 'longitude': -76, }

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(403, response.status_code)

        response = self.client.get(targets_url)
        self.assertEqual(403, response.status_code)


class TestGetTarget(TestCase):
    """Tests GETing the targets view."""

    def setUp(self):
        """Creates user and logs in."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')

        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

    def test_no_targets(self):
        """We get back an empty list if we have no targets."""
        response = self.client.get(targets_url)
        self.assertEqual(200, response.status_code)

        self.assertEqual([], json.loads(response.content))

    def test_get_targets(self):
        """We get back the targets we own."""
        t1 = Target(user=self.user, target_type=TargetType.standard)
        t1.save()

        t2 = Target(user=self.user, target_type=TargetType.standard)
        t2.save()

        response = self.client.get(targets_url)
        self.assertEqual(200, response.status_code)

        d = json.loads(response.content)

        self.assertItemsEqual([t1.json(), t2.json()], d)

    def test_not_others(self):
        """We don't get targets owned by other users."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')

        mine = Target(user=self.user, target_type=TargetType.standard)
        mine.save()

        theirs = Target(user=user2, target_type=TargetType.standard)
        theirs.save()

        response = self.client.get(targets_url)
        self.assertEqual(200, response.status_code)

        d = json.loads(response.content)

        self.assertItemsEqual([mine.json()], d)


class TestPostTarget(TestCase):
    """Tests POSTing the targets view."""

    def setUp(self):
        """Creates user and logs in."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')

        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

    def test_complete(self):
        """Send complete target with all fields."""
        target = {
            'type': 'standard',
            'latitude': 38,
            'longitude': -76,
            'orientation': 'n',
            'shape': 'square',
            'background_color': 'white',
            'alphanumeric': 'ABC',
            'alphanumeric_color': 'black',
            'description': 'Best target',
            'autonomous': False,
        }

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)

        # Check that returned target matches
        created = json.loads(response.content)

        self.assertEqual(target['type'], created['type'])
        self.assertEqual(target['latitude'], created['latitude'])
        self.assertEqual(target['longitude'], created['longitude'])
        self.assertEqual(target['orientation'], created['orientation'])
        self.assertEqual(target['shape'], created['shape'])
        self.assertEqual(target['background_color'],
                         created['background_color'])
        self.assertEqual(target['alphanumeric'], created['alphanumeric'])
        self.assertEqual(target['alphanumeric_color'],
                         created['alphanumeric_color'])
        self.assertEqual(target['description'], created['description'])
        self.assertEqual(target['autonomous'], created['autonomous'])

        # It also contains 'user' and 'id' fields.
        self.assertIn('id', created)
        self.assertIn('user', created)

    def test_minimal(self):
        """Send target minimal fields."""
        target = {'type': 'standard'}

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)

        # Check that returned target matches
        created = json.loads(response.content)

        self.assertEqual(target['type'], created['type'])
        self.assertEqual(None, created['latitude'])
        self.assertEqual(None, created['longitude'])
        self.assertEqual(None, created['orientation'])
        self.assertEqual(None, created['shape'])
        self.assertEqual(None, created['background_color'])
        self.assertEqual(None, created['alphanumeric'])
        self.assertEqual(None, created['alphanumeric_color'])
        self.assertEqual(None, created['description'])
        self.assertEqual(False, created['autonomous'])

        # It also contains 'user' and 'id' fields.
        self.assertIn('id', created)
        self.assertIn('user', created)

    def test_none(self):
        """Send target with None fields has no effect."""
        target = {'type': 'standard', 'latitude': None, 'shape': None}

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)

        # Check that returned target matches
        created = json.loads(response.content)

        self.assertEqual(target['type'], created['type'])
        self.assertEqual(None, created['latitude'])
        self.assertEqual(None, created['shape'])

    def test_missing_type(self):
        """Target type required."""
        target = {
            'latitude': 38,
            'longitude': -76,
            'orientation': 'N',
            'shape': 'square',
            'background_color': 'white',
            'alphanumeric': 'ABC',
            'alphanumeric_color': 'black',
            'description': 'Best target',
        }

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_invalid_json(self):
        """Request body must contain valid JSON."""
        response = self.client.post(targets_url,
                                    data='type=standard&longitude=-76',
                                    content_type='multipart/form-data')
        self.assertEqual(400, response.status_code)

    def test_missing_latitude(self):
        """Target latitude required if longitude specified."""
        target = {'type': 'standard', 'longitude': -76}

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_missing_longitude(self):
        """Target longitude required if latitude specified."""
        target = {'type': 'standard', 'latitude': 38}

        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_invalid_type(self):
        """Send bad target type."""
        bad = ['foo', 'standard nonsense', 42]

        for b in bad:
            target = {'type': b, 'latitude': 38, 'longitude': -76}

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_latitude(self):
        """Send bad target latitude."""
        bad = ['string', 120, -120]

        for b in bad:
            target = {'type': 'standard', 'latitude': b, 'longitude': -76}

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_longitude(self):
        """Send bad target longitude."""
        bad = ['string', 200, -200]

        for b in bad:
            target = {'type': 'standard', 'latitude': 38, 'longitude': b}

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_shape(self):
        """Send bad target shape."""
        bad = ['square circle', 'dodecahedron', 42]

        for b in bad:
            target = {
                'type': 'standard',
                'latitude': 38,
                'longitude': -76,
                'shape': b,
            }

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_background_color(self):
        """Send bad target background color."""
        bad = ['white black', 'mahogany', 42]

        for b in bad:
            target = {
                'type': 'standard',
                'latitude': 38,
                'longitude': -76,
                'background_color': b,
            }

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_alphanumeric_color(self):
        """Send bad target alphanumeric color."""
        bad = ['white black', 'mahogany', 42]

        for b in bad:
            target = {
                'type': 'standard',
                'latitude': 38,
                'longitude': -76,
                'alphanumeric_color': b,
            }

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_orientation(self):
        """Send bad target orientation."""
        bad = ['NNE', 'north', 42]

        for b in bad:
            target = {
                'type': 'standard',
                'latitude': 38,
                'longitude': -76,
                'orientation': b,
            }

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_autonomous(self):
        """Send bad target autonomous."""
        bad = ['true', 1, 'Yes']

        for b in bad:
            target = {
                'type': 'standard',
                'latitude': 38,
                'longitude': -76,
                'autonomous': b,
            }

            response = self.client.post(targets_url,
                                        data=json.dumps(target),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_create_target_team_id(self):
        """Request fails if non-admin user specifies team_id."""
        target = {'type': 'standard', 'team_id': self.user.username}
        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(403, response.status_code)

    def test_superuser_create_target(self):
        """Admin user can create target on behalf of another team."""
        # Login as superuser.
        superuser = User.objects.create_superuser(
            'testsuperuser', 'testsuperemail@x.com', 'testsuperpass')
        response = self.client.post(login_url, {
            'username': 'testsuperuser',
            'password': 'testsuperpass'
        })
        self.assertEqual(200, response.status_code)

        # Create target.
        target = {'type': 'standard', 'team_id': self.user.username}
        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)

        # Ensure target created for proper user.
        created = json.loads(response.content)
        self.assertEqual(self.user.id, created['user'])

    def test_actionable_override(self):
        """Request fails if non-admin user specifies actionable_override."""
        target = {'type': 'standard', 'actionable_override': True}
        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(403, response.status_code)

    def test_superuser_actionable_override(self):
        """Admin user can set actionable_override flag."""
        # Login as superuser.
        superuser = User.objects.create_superuser(
            'testsuperuser', 'testsuperemail@x.com', 'testsuperpass')
        response = self.client.post(login_url, {
            'username': 'testsuperuser',
            'password': 'testsuperpass'
        })
        self.assertEqual(200, response.status_code)

        # Create target.
        target = {'type': 'standard', 'actionable_override': True}
        response = self.client.post(targets_url,
                                    data=json.dumps(target),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)

        # Ensure target has actionable_override flag set.
        created = json.loads(response.content)
        self.assertEqual(True, created['actionable_override'])


class TestTargetsIdLoggedOut(TestCase):
    """Tests logged out targets_id."""

    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        response = self.client.get(targets_id_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestTargetId(TestCase):
    """Tests GET/PUT/DELETE specific targets."""

    def setUp(self):
        """Creates user and logs in."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')

        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

    def test_get_nonexistent(self):
        """Test GETting a target that doesn't exist."""
        response = self.client.get(targets_id_url(args=[999]))
        self.assertEqual(404, response.status_code)

    def test_get_other_user(self):
        """Test GETting a target owned by a different user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Target(user=user2, target_type=TargetType.standard)
        t.save()

        response = self.client.get(targets_id_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_get_own(self):
        """Test GETting a target owned by the correct user."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        response = self.client.get(targets_id_url(args=[t.pk]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(t.json(), json.loads(response.content))

    def test_put_append(self):
        """PUT sets a new field that wasn't set before."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'description': 'Hello'}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual('Hello', t.description)

        # Response also matches
        self.assertEqual(t.json(), json.loads(response.content))

    def test_put_one(self):
        """PUT update one field without affecting others."""
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
                   description='Test target')
        t.save()

        data = {'shape': 'circle'}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        t.location.refresh_from_db()
        self.assertEqual(self.user, t.user)
        self.assertEqual(TargetType.standard, t.target_type)
        self.assertEqual(38, t.location.latitude)
        self.assertEqual(-76, t.location.longitude)
        self.assertEqual(Orientation.s, t.orientation)
        self.assertEqual(Shape.circle, t.shape)
        self.assertEqual(Color.white, t.background_color)
        self.assertEqual('ABC', t.alphanumeric)
        self.assertEqual(Color.black, t.alphanumeric_color)
        self.assertEqual('Test target', t.description)

    def test_put_clear_shape(self):
        """PUT clear a field with None."""
        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   shape=Shape.square)
        t.save()

        data = {'shape': None}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(None, t.shape)

    def test_put_clear_type(self):
        """PUT type may not be cleared."""
        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   shape=Shape.square)
        t.save()

        data = {'type': None}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(400, response.status_code)

    def test_put_location(self):
        """PUT new location"""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'latitude': 38, 'longitude': -76}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(38, t.location.latitude)
        self.assertEqual(-76, t.location.longitude)

    def test_put_location_missing_one(self):
        """PUTting new location requires both latitude and longitude."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'latitude': 38}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(400, response.status_code)

    def test_put_update_location(self):
        """PUT updating location only requires one of lat/lon."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user, target_type=TargetType.standard, location=l)
        t.save()

        data = {'latitude': 39}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        t.location.refresh_from_db()
        self.assertEqual(39, t.location.latitude)
        self.assertEqual(-76, t.location.longitude)

    def test_put_clear_location(self):
        """PUT clear location by clearing lat and lon."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user, target_type=TargetType.standard, location=l)
        t.save()

        data = {'latitude': None, 'longitude': None}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(None, t.location)

    def test_put_partial_clear_location(self):
        """PUT can't clear location with only one of lat/lon."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user, target_type=TargetType.standard, location=l)
        t.save()

        data = {'latitude': None}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(400, response.status_code)

    def test_put_invalid_json(self):
        """PUT request body must be valid JSON."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user, target_type=TargetType.standard, location=l)
        t.save()

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data="latitude=76",
            content_type='multipart/form-data')
        self.assertEqual(400, response.status_code)

    def test_put_change_autonomous(self):
        """Change autonomous with PUT"""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'autonomous': True}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(True, t.autonomous)

    def test_put_change_actionable_override(self):
        """PUT fails if non-admin user tries to change actionable_override."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'actionable_override': True}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(403, response.status_code)

    def test_put_superuser_change_actionable_override(self):
        """Admin user can update actionable_override flag."""
        # Login as superuser.
        superuser = User.objects.create_superuser(
            'testsuperuser', 'testsuperemail@x.com', 'testsuperpass')
        response = self.client.post(login_url, {
            'username': 'testsuperuser',
            'password': 'testsuperpass'
        })
        self.assertEqual(200, response.status_code)

        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        data = {'actionable_override': True}

        response = self.client.put(
            targets_id_url(args=[t.pk]),
            data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(True, t.actionable_override)

    def test_delete_own(self):
        """Test DELETEing a target owned by the correct user."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        pk = t.pk

        self.assertTrue(Target.objects.get(pk=pk))

        response = self.client.delete(targets_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        with self.assertRaises(Target.DoesNotExist):
            Target.objects.get(pk=pk)

    def test_delete_other(self):
        """Test DELETEing a target owned by another user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Target(user=user2, target_type=TargetType.standard)
        t.save()

        response = self.client.delete(targets_id_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_get_after_delete_own(self):
        """Test GETting a target after DELETE."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        pk = t.pk

        response = self.client.delete(targets_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        response = self.client.get(targets_id_url(args=[pk]))
        self.assertEqual(404, response.status_code)

    def test_delete_thumb(self):
        """Test DELETEing a target with thumbnail."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        pk = t.pk

        with open(test_image("A.jpg")) as f:
            response = self.client.post(
                targets_id_image_url(args=[pk]),
                data=f.read(),
                content_type="image/jpeg")
            self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        thumb = t.thumbnail.path
        self.assertTrue(os.path.exists(thumb))

        response = self.client.delete(targets_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        self.assertFalse(os.path.exists(thumb))


def test_image(name):
    """Compute path of test image"""
    return os.path.join(settings.BASE_DIR, 'auvsi_suas/fixtures/testdata',
                        name)


class TestTargetIdImage(TestCase):
    """Tests GET/PUT/DELETE target image."""

    def setUp(self):
        """Creates user and logs in."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')

        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

        # Create a target
        response = self.client.post(targets_url,
                                    data=json.dumps({'type': 'standard'}),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)
        self.target_id = json.loads(response.content)['id']

    def test_get_no_image(self):
        """404 when GET image before upload."""
        response = self.client.get(targets_id_image_url(args=[self.target_id]))
        self.assertEqual(404, response.status_code)

    def test_delete_no_image(self):
        """404 when DELETE image before upload."""
        response = self.client.delete(
                targets_id_image_url(args=[self.target_id]))  # yapf: disable
        self.assertEqual(404, response.status_code)

    def test_get_other_user(self):
        """Test GETting a thumbnail owned by a different user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Target(user=user2, target_type=TargetType.standard)
        t.save()

        response = self.client.get(targets_id_image_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_post_bad_image(self):
        """Try to upload bad image"""
        response = self.client.post(
            targets_id_image_url(args=[self.target_id]),
            data='Hahaha',
            content_type='image/jpeg')
        self.assertEqual(400, response.status_code)

    def post_image(self, name, content_type='image/jpeg'):
        """POST image, assert that it worked"""
        with open(test_image(name)) as f:
            response = self.client.post(
                targets_id_image_url(args=[self.target_id]),
                data=f.read(),
                content_type=content_type)
            self.assertEqual(200, response.status_code)

    def test_post_jpg(self):
        """Successfully upload jpg"""
        self.post_image('S.jpg')

    def test_post_png(self):
        """Successfully upload png"""
        self.post_image('A.png', content_type='image/png')

    def test_post_gif(self):
        """GIF upload not allowed"""
        with open(test_image('A.gif')) as f:
            response = self.client.post(
                targets_id_image_url(args=[self.target_id]),
                data=f.read(),
                content_type='image/gif')
            self.assertEqual(400, response.status_code)

    def test_get_image(self):
        """Successfully GET uploaded image"""
        self.post_image('S.jpg')

        response = self.client.get(targets_id_image_url(args=[self.target_id]))
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/jpeg', response['Content-Type'])

        data = ''.join(response.streaming_content)

        # Did we get back what we uploaded?
        with open(test_image('S.jpg')) as f:
            self.assertEqual(f.read(), data)

    def test_replace_image(self):
        """Successfully replace uploaded image"""
        self.post_image('S.jpg')
        self.post_image('A.jpg')

        response = self.client.get(targets_id_image_url(args=[self.target_id]))
        self.assertEqual(200, response.status_code)

        data = ''.join(response.streaming_content)

        # Did we replace it?
        with open(test_image('A.jpg')) as f:
            self.assertEqual(f.read(), data)

    def test_put_image(self):
        """PUT works just like POST"""
        with open(test_image('S.jpg')) as f:
            response = self.client.put(
                targets_id_image_url(args=[self.target_id]),
                data=f.read(),
                content_type='image/jpeg')
            self.assertEqual(200, response.status_code)

        response = self.client.get(targets_id_image_url(args=[self.target_id]))
        self.assertEqual(200, response.status_code)

        data = ''.join(response.streaming_content)

        # Did we get back what we uploaded?
        with open(test_image('S.jpg')) as f:
            self.assertEqual(f.read(), data)

    def test_post_delete_old(self):
        """Old image deleted when new doesn't overwrite."""
        self.post_image('A.jpg')

        t = Target.objects.get(pk=self.target_id)
        jpg_path = t.thumbnail.path
        self.assertTrue(os.path.exists(jpg_path))

        self.post_image('A.png', content_type='image/png')
        self.assertFalse(os.path.exists(jpg_path))

    def test_delete(self):
        """Image deleted on DELETE"""
        self.post_image('A.jpg')

        t = Target.objects.get(pk=self.target_id)
        jpg_path = t.thumbnail.path
        self.assertTrue(os.path.exists(jpg_path))

        response = self.client.delete(targets_id_image_url(args=[self.target_id
                                                                 ]))
        self.assertEqual(200, response.status_code)

        self.assertFalse(os.path.exists(jpg_path))

    def test_get_after_delete(self):
        """GET returns 404 after DELETE"""
        self.post_image('A.jpg')

        response = self.client.delete(targets_id_image_url(args=[self.target_id
                                                                 ]))
        self.assertEqual(200, response.status_code)

        response = self.client.get(targets_id_image_url(args=[self.target_id]))
        self.assertEqual(404, response.status_code)


class TestTargetsAdminReviewNotAdmin(TestCase):
    """Tests admin review when not logged in as admin."""

    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        response = self.client.get(targets_review_url)
        self.assertEqual(403, response.status_code)

        response = self.client.put(targets_review_id_url(args=[1]))
        self.assertEqual(403, response.status_code)

    def test_not_admin(self):
        """Unauthenticated requests should fail."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

        response = self.client.get(targets_review_url)
        self.assertEqual(403, response.status_code)

        response = self.client.put(targets_review_id_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestTargetsAdminReview(TestCase):
    """Tests GET/PUT admin review of targets."""

    def setUp(self):
        """Creates user and logs in."""
        self.user = User.objects.create_superuser(
            'testuser', 'testemail@x.com', 'testpass')
        self.team = User.objects.create_user('testuser2', 'testemail@x.com',
                                             'testpass')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(200, response.status_code)

    def test_get_no_targets(self):
        """Test GET when there are no targets."""
        response = self.client.get(targets_review_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.content))

    def test_get_editable_targets(self):
        """Test GET when there are targets but are still in editable window."""
        MissionClockEvent(user=self.team,
                          team_on_clock=True,
                          team_on_timeout=False).save()
        Target(user=self.team, target_type=TargetType.standard).save()

        response = self.client.get(targets_review_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.content))

    def test_get_noneditable_without_thumbnail_targets(self):
        """Test GET when there are non-editable targets without thumbnail."""
        MissionClockEvent(user=self.team,
                          team_on_clock=True,
                          team_on_timeout=False).save()
        MissionClockEvent(user=self.team,
                          team_on_clock=False,
                          team_on_timeout=False).save()
        target = Target(user=self.team, target_type=TargetType.standard)
        target.save()

        response = self.client.get(targets_review_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(0, len(data))

    def test_get_noneditable_targets(self):
        """Test GET when there are non-editable targets."""
        MissionClockEvent(user=self.team,
                          team_on_clock=True,
                          team_on_timeout=False).save()
        MissionClockEvent(user=self.team,
                          team_on_clock=False,
                          team_on_timeout=False).save()
        target = Target(user=self.team, target_type=TargetType.standard)
        target.save()

        with open(test_image('A.jpg')) as f:
            target.thumbnail.save('%d.%s' % (target.pk, 'jpg'), ImageFile(f))
        target.save()

        response = self.client.get(targets_review_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertIn('type', data[0])
        self.assertEqual('standard', data[0]['type'])

    def test_put_review_no_approved(self):
        """Test PUT review with no approved field."""
        target = Target(user=self.team, target_type=TargetType.standard)
        target.save()

        response = self.client.put(targets_review_id_url(args=[target.pk]))
        self.assertEqual(400, response.status_code)

    def test_put_invalid_pk(self):
        """Test PUT reivew with invalid pk."""
        response = self.client.put(
            targets_review_id_url(args=[1]),
            data=json.dumps({
                'thumbnail_approved': True,
                'description_approved': True,
            }))
        self.assertEqual(404, response.status_code)

    def test_put_review(self):
        """Test PUT review is saved."""
        target = Target(user=self.team, target_type=TargetType.standard)
        target.save()

        response = self.client.put(
            targets_review_id_url(args=[target.pk]),
            data=json.dumps({
                'thumbnail_approved': True,
                'description_approved': True,
            }))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertEqual(target.pk, data['id'])
        self.assertIn('thumbnail_approved', data)
        self.assertTrue(data['thumbnail_approved'])
        self.assertTrue(data['description_approved'])

        target.refresh_from_db()
        self.assertTrue(target.thumbnail_approved)
        self.assertTrue(target.description_approved)
