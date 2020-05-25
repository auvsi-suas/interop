"""Tests for the missions module."""

import functools
import json
import os.path
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.odlc import Odlc
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.proto import interop_api_pb2
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.test import TestCase
from django.urls import reverse

odlcs_url = reverse('auvsi_suas:odlcs')
odlcs_id_url = functools.partial(reverse, 'auvsi_suas:odlcs_id')
odlcs_id_image_url = functools.partial(reverse, 'auvsi_suas:odlcs_id_image')
odlcs_review_url = reverse('auvsi_suas:odlcs_review')
odlcs_review_id_url = functools.partial(reverse, 'auvsi_suas:odlcs_review_id')


class TestOdlcsCommon(TestCase):
    """Common functionality for ODLC tests."""
    def setUp(self):
        # Mission
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        wpt = Waypoint()
        wpt.order = 10
        wpt.latitude = 10
        wpt.longitude = 100
        wpt.altitude_msl = 0
        wpt.save()
        self.mission = MissionConfig()
        self.mission.home_pos = pos
        self.mission.lost_comms_pos = pos
        self.mission.emergent_last_known_pos = pos
        self.mission.off_axis_odlc_pos = pos
        self.mission.air_drop_pos = pos
        self.mission.ugv_drive_pos = pos
        self.mission.save()
        self.mission.mission_waypoints.add(wpt)
        self.mission.search_grid_points.add(wpt)
        self.mission.save()
        # Mission 2
        self.mission2 = MissionConfig()
        self.mission2.home_pos = pos
        self.mission2.lost_comms_pos = pos
        self.mission2.emergent_last_known_pos = pos
        self.mission2.off_axis_odlc_pos = pos
        self.mission2.air_drop_pos = pos
        self.mission2.ugv_drive_pos = pos
        self.mission2.save()
        self.mission2.mission_waypoints.add(wpt)
        self.mission2.search_grid_points.add(wpt)
        self.mission2.save()


class TestOdlcsLoggedOut(TestOdlcsCommon):
    """Tests logged out odlcs."""
    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        odlc = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'latitude': 38,
            'longitude': -76,
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(403, response.status_code)

        response = self.client.get(odlcs_url)
        self.assertEqual(403, response.status_code)


class TestGetOdlc(TestOdlcsCommon):
    """Tests GETing the odlcs view."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestGetOdlc, self).setUp()
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.client.force_login(self.user)

    def test_no_odlcs(self):
        """We get back an empty list if we have no odlcs."""
        response = self.client.get(odlcs_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.content))

    def test_get_odlcs(self):
        """We get back the odlcs we own."""
        t1 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t1.save()

        t2 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t2.save()

        t3 = Odlc(mission=self.mission,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.EMERGENT)
        t3.save()

        t4 = Odlc(mission=self.mission2,
                  user=self.user,
                  odlc_type=interop_api_pb2.Odlc.STANDARD)
        t4.save()

        get_id = lambda x: x['id']
        response = self.client.get(odlcs_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            sorted([
                {
                    'id': t4.pk,
                    'mission': self.mission2.pk,
                    'type': 'STANDARD',
                    'autonomous': False,
                },
                {
                    'id': t3.pk,
                    'mission': self.mission.pk,
                    'type': 'EMERGENT',
                    'autonomous': False,
                },
                {
                    'id': t2.pk,
                    'mission': self.mission.pk,
                    'type': 'STANDARD',
                    'autonomous': False,
                },
                {
                    'id': t1.pk,
                    'mission': self.mission.pk,
                    'type': 'STANDARD',
                    'autonomous': False,
                },
            ],
                   key=get_id), sorted(json.loads(response.content),
                                       key=get_id))

        response = self.client.get(odlcs_url +
                                   '?mission=%d' % self.mission2.pk)
        self.assertEqual(200, response.status_code)
        self.assertEqual([
            {
                'id': t4.pk,
                'mission': self.mission2.pk,
                'type': 'STANDARD',
                'autonomous': False,
            },
        ], json.loads(response.content))

    def test_not_others(self):
        """We don't get odlcs owned by other users."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')

        mine = Odlc(mission=self.mission,
                    user=self.user,
                    odlc_type=interop_api_pb2.Odlc.STANDARD)
        mine.save()
        theirs = Odlc(mission=self.mission,
                      user=user2,
                      odlc_type=interop_api_pb2.Odlc.STANDARD)
        theirs.save()

        response = self.client.get(odlcs_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([
            {
                'id': mine.pk,
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'autonomous': False,
            },
        ], json.loads(response.content))


class TestPostOdlc(TestOdlcsCommon):
    """Tests POSTing the odlcs view."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestPostOdlc, self).setUp()
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()
        self.client.force_login(self.user)

    def test_complete(self):
        """Send complete odlc with all fields."""
        odlc = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'latitude': 38,
            'longitude': -76,
            'orientation': 'N',
            'shape': 'SQUARE',
            'shapeColor': 'WHITE',
            'alphanumeric': 'A',
            'alphanumericColor': 'BLACK',
            'description': 'Best odlc',
            'autonomous': False,
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(200, response.status_code)

        # Check that returned odlc matches
        created = json.loads(response.content)

        self.assertIn('id', created)
        self.assertIn('mission', created)
        self.assertEqual(self.mission.pk, created['mission'])
        self.assertEqual(odlc['type'], created['type'])
        self.assertEqual(odlc['latitude'], created['latitude'])
        self.assertEqual(odlc['longitude'], created['longitude'])
        self.assertEqual(odlc['orientation'], created['orientation'])
        self.assertEqual(odlc['shape'], created['shape'])
        self.assertEqual(odlc['shapeColor'], created['shapeColor'])
        self.assertEqual(odlc['alphanumeric'], created['alphanumeric'])
        self.assertEqual(odlc['alphanumericColor'],
                         created['alphanumericColor'])
        self.assertEqual(odlc['description'], created['description'])
        self.assertEqual(odlc['autonomous'], created['autonomous'])

    def test_minimal(self):
        """Send odlc minimal fields."""
        odlc = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(200, response.status_code)

        # Check that returned odlc matches
        created = json.loads(response.content)

        self.assertIn('id', created)
        self.assertEqual(odlc['type'], created['type'])
        self.assertNotIn('latitude', created)
        self.assertNotIn('longitude', created)
        self.assertNotIn('orientation', created)
        self.assertNotIn('shape', created)
        self.assertNotIn('shapeColor', created)
        self.assertNotIn('alphanumeric', created)
        self.assertNotIn('alphanumericColor', created)
        self.assertNotIn('description', created)
        self.assertEqual(False, created['autonomous'])

    def test_missing_type(self):
        """Odlc type required."""
        odlc = {
            'mission': self.mission.pk,
            'latitude': 38,
            'longitude': -76,
            'orientation': 'N',
            'shape': 'SQUARE',
            'shapeColor': 'WHITE',
            'alphanumeric': 'A',
            'alphanumericColor': 'BLACK',
            'description': 'Best odlc',
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_invalid_json(self):
        """Request body must contain valid JSON."""
        response = self.client.post(odlcs_url,
                                    data='type=STANDARD&longitude=-76',
                                    content_type='multipart/form-data')
        self.assertEqual(400, response.status_code)

    def test_invalid_mission(self):
        """Mission ID must correspond to an actual mission."""
        odlc = {
            'mission': self.mission2.pk + 1,
            'type': 'STANDARD',
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_missing_latitude(self):
        """Odlc latitude required if longitude specified."""
        odlc = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'longitude': -76
        }

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_missing_longitude(self):
        """Odlc longitude required if latitude specified."""
        odlc = {'type': 'STANDARD', 'latitude': 38}

        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_invalid_type(self):
        """Send bad odlc type."""
        bad = ['foo', 'STANDARD nonsense', 42]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': b,
                'latitude': 38,
                'longitude': -76
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_latitude(self):
        """Send bad odlc latitude."""
        bad = ['string', 120, -120]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'latitude': b,
                'longitude': -76
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_longitude(self):
        """Send bad odlc longitude."""
        bad = ['string', 200, -200]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'latitude': 38,
                'longitude': b
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_shape(self):
        """Send bad odlc shape."""
        bad = ['square circle', 'dodecahedron', 42]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'shape': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_shape_color(self):
        """Send bad odlc background color."""
        bad = ['white black', 'mahogany', 42]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'shapeColor': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_alphanumeric(self):
        """Send bad alphanumerics."""
        bad = ['a', '10', 'AA']

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'alphanumeric': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_alphanumeric_color(self):
        """Send bad odlc alphanumeric color."""
        bad = ['white black', 'mahogany', 42]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'alphanumericColor': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_orientation(self):
        """Send bad odlc orientation."""
        bad = ['NNE', 'north', 42]

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'orientation': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_invalid_autonomous(self):
        """Send bad odlc autonomous."""
        bad = ['true', 1, 'Yes']

        for b in bad:
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
                'autonomous': b,
            }

            response = self.client.post(odlcs_url,
                                        data=json.dumps(odlc),
                                        content_type='application/json')
            self.assertEqual(400, response.status_code)

    def test_too_many(self):
        """Too many uploads."""
        too_many = 50

        # Uploaded too many for mission 1.
        for _ in range(too_many):
            odlc = {
                'mission': self.mission.pk,
                'type': 'STANDARD',
            }
            self.client.post(odlcs_url,
                             data=json.dumps(odlc),
                             content_type='application/json')

        # Upload past too many should fail.
        odlc = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
        }
        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

        # An upload for mission 2 should succeed.
        odlc = {
            'mission': self.mission2.pk,
            'type': 'STANDARD',
        }
        response = self.client.post(odlcs_url,
                                    data=json.dumps(odlc),
                                    content_type='application/json')
        self.assertEqual(200, response.status_code)


class TestOdlcsIdLoggedOut(TestOdlcsCommon):
    """Tests logged out odlcs_id."""
    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        response = self.client.get(odlcs_id_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestOdlcId(TestOdlcsCommon):
    """Tests GET/PUT/DELETE specific odlcs."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestOdlcId, self).setUp()
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.client.force_login(self.user)

    def test_get_nonexistent(self):
        """Test GETting a odlc that doesn't exist."""
        response = self.client.get(odlcs_id_url(args=[999]))
        self.assertEqual(404, response.status_code)

    def test_get_other_user(self):
        """Test GETting a odlc owned by a different user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Odlc(mission=self.mission,
                 user=user2,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        response = self.client.get(odlcs_id_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_get_own(self):
        """Test GETting a odlc owned by the correct user."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        response = self.client.get(odlcs_id_url(args=[t.pk]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(
            {
                'mission': self.mission.pk,
                'id': t.pk,
                'type': 'STANDARD',
                'autonomous': False,
            }, json.loads(response.content))

    def test_put_append(self):
        """PUT sets a new field that wasn't set before."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        data = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'description': 'Hello'
        }

        response = self.client.put(odlcs_id_url(args=[t.pk]),
                                   data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual('Hello', t.description)

    def test_put_changes_last_modified(self):
        """PUT sets a new field that wasn't set before."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()
        orig_last_modified = t.last_modified_time

        data = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'description': 'Hello'
        }

        response = self.client.put(odlcs_id_url(args=[t.pk]),
                                   data=json.dumps(data))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertNotEqual(orig_last_modified, t.last_modified_time)

    def test_put_updates_fields(self):
        """PUT updates fields."""
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
                 description='Test odlc')
        t.save()

        updated = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
            'latitude': 39,
            'longitude': -77,
            'orientation': 'N',
            'shape': 'CIRCLE',
            'shapeColor': 'BLACK',
            'alphanumeric': 'A',
            'alphanumericColor': 'GREEN',
            'description': 'Best odlc',
            'autonomous': False,
        }

        response = self.client.put(odlcs_id_url(args=[t.pk]),
                                   data=json.dumps(updated))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        t.location.refresh_from_db()
        self.assertEqual(self.user, t.user)
        self.assertEqual(interop_api_pb2.Odlc.STANDARD, t.odlc_type)
        self.assertEqual(39, t.location.latitude)
        self.assertEqual(-77, t.location.longitude)
        self.assertEqual(interop_api_pb2.Odlc.N, t.orientation)
        self.assertEqual(interop_api_pb2.Odlc.CIRCLE, t.shape)
        self.assertEqual(interop_api_pb2.Odlc.BLACK, t.shape_color)
        self.assertEqual('A', t.alphanumeric)
        self.assertEqual(interop_api_pb2.Odlc.GREEN, t.alphanumeric_color)
        self.assertEqual('Best odlc', t.description)

    def test_put_clear_shape(self):
        """PUT clear a field with None."""
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
                 description='Test odlc')
        t.save()

        updated = {
            'mission': self.mission.pk,
            'type': 'STANDARD',
        }

        response = self.client.put(odlcs_id_url(args=[t.pk]),
                                   data=json.dumps(updated))
        self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        self.assertEqual(self.user, t.user)
        self.assertEqual(interop_api_pb2.Odlc.STANDARD, t.odlc_type)
        self.assertIsNone(t.location)
        self.assertIsNone(t.orientation)
        self.assertIsNone(t.shape)
        self.assertIsNone(t.shape_color)
        self.assertEqual('', t.alphanumeric)
        self.assertIsNone(t.alphanumeric_color)
        self.assertEqual('', t.description)

    def test_delete_own(self):
        """Test DELETEing a odlc owned by the correct user."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        pk = t.pk

        self.assertTrue(Odlc.objects.get(pk=pk))

        response = self.client.delete(odlcs_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        with self.assertRaises(Odlc.DoesNotExist):
            Odlc.objects.get(pk=pk)

    def test_delete_other(self):
        """Test DELETEing a odlc owned by another user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Odlc(mission=self.mission,
                 user=user2,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        response = self.client.delete(odlcs_id_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_get_after_delete_own(self):
        """Test GETting a odlc after DELETE."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        pk = t.pk

        response = self.client.delete(odlcs_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        response = self.client.get(odlcs_id_url(args=[pk]))
        self.assertEqual(404, response.status_code)

    def test_delete_thumb(self):
        """Test DELETEing a odlc with thumbnail."""
        t = Odlc(mission=self.mission,
                 user=self.user,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        pk = t.pk

        with open(test_image("A.jpg"), 'rb') as f:
            response = self.client.post(odlcs_id_image_url(args=[pk]),
                                        data=f.read(),
                                        content_type="image/jpeg")
            self.assertEqual(200, response.status_code)

        t.refresh_from_db()
        thumb = t.thumbnail.path
        self.assertTrue(os.path.exists(thumb))

        response = self.client.delete(odlcs_id_url(args=[pk]))
        self.assertEqual(200, response.status_code)

        self.assertFalse(os.path.exists(thumb))


def test_image(name):
    """Compute path of test image"""
    return os.path.join(settings.BASE_DIR, 'auvsi_suas/testdata', name)


class TestOdlcIdImage(TestOdlcsCommon):
    """Tests GET/PUT/DELETE odlc image."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestOdlcIdImage, self).setUp()
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.client.force_login(self.user)

        # Create a odlc
        response = self.client.post(odlcs_url,
                                    data=json.dumps({
                                        'mission': self.mission.pk,
                                        'type': 'STANDARD'
                                    }),
                                    content_type='application/json')
        self.assertEqual(200, response.status_code)
        self.odlc_id = json.loads(response.content)['id']
        self.odlc = Odlc.objects.get(pk=self.odlc_id)

    def test_get_no_image(self):
        """404 when GET image before upload."""
        response = self.client.get(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(404, response.status_code)

    def test_delete_no_image(self):
        """404 when DELETE image before upload."""
        response = self.client.delete(
                odlcs_id_image_url(args=[self.odlc_id]))  # yapf: disable
        self.assertEqual(404, response.status_code)

    def test_get_other_user(self):
        """Test GETting a thumbnail owned by a different user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        t = Odlc(mission=self.mission,
                 user=user2,
                 odlc_type=interop_api_pb2.Odlc.STANDARD)
        t.save()

        response = self.client.get(odlcs_id_image_url(args=[t.pk]))
        self.assertEqual(403, response.status_code)

    def test_post_bad_image(self):
        """Try to upload bad image"""
        response = self.client.post(odlcs_id_image_url(args=[self.odlc_id]),
                                    data='Hahaha',
                                    content_type='image/jpeg')
        self.assertEqual(400, response.status_code)

    def upload_image(self, name, method='POST', content_type='image/jpeg'):
        """Upload image, assert that it worked"""
        # Read image to upload.
        data = None
        with open(test_image(name), 'rb') as f:
            data = f.read()

        # Upload image.
        response = None
        if method == 'POST':
            response = self.client.post(
                odlcs_id_image_url(args=[self.odlc_id]),
                data=data,
                content_type=content_type)
        else:
            response = self.client.put(odlcs_id_image_url(args=[self.odlc_id]),
                                       data=data,
                                       content_type=content_type)
        self.assertEqual(200, response.status_code)

        # Validate can retrieve image with uploaded contents.
        response = self.client.get(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(200, response.status_code)
        resp_data = b''.join(response.streaming_content)
        self.assertEqual(data, resp_data)

    def test_post_jpg(self):
        """Successfully upload jpg"""
        self.upload_image('S.jpg')

    def test_post_png(self):
        """Successfully upload png"""
        self.upload_image('A.png', content_type='image/png')

    def test_post_gif(self):
        """GIF upload not allowed"""
        with open(test_image('A.gif'), 'rb') as f:
            response = self.client.post(
                odlcs_id_image_url(args=[self.odlc_id]),
                data=f.read(),
                content_type='image/gif')
            self.assertEqual(400, response.status_code)

    def test_get_image(self):
        """Successfully GET uploaded image"""
        self.upload_image('S.jpg')

        response = self.client.get(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/jpeg', response['Content-Type'])

        data = b''.join(response.streaming_content)

        # Did we get back what we uploaded?
        with open(test_image('S.jpg'), 'rb') as f:
            self.assertEqual(f.read(), data)

    def test_replace_image(self):
        """Successfully replace uploaded image"""
        self.upload_image('S.jpg')
        self.upload_image('A.jpg')

    def test_put_image(self):
        """PUT works just like POST"""
        self.upload_image('S.jpg', method='PUT')

    def test_update_invalidates_thumbnail_review(self):
        """Test that update invalidates thumbnail field."""
        self.odlc.thumbnail_approved = True
        self.odlc.save()

        # POST
        self.upload_image('A.jpg')
        self.odlc.refresh_from_db()
        self.assertIsNone(self.odlc.thumbnail_approved)

        self.odlc.thumbnail_approved = True
        self.odlc.description_approved = True
        self.odlc.save()

        # PUT
        self.upload_image('A.jpg', method='PUT')
        self.odlc.refresh_from_db()
        self.assertIsNone(self.odlc.thumbnail_approved)

        self.odlc.thumbnail_approved = True
        self.odlc.description_approved = True
        self.odlc.save()

        # DELETE
        response = self.client.delete(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(200, response.status_code)
        self.odlc.refresh_from_db()
        self.assertIsNone(self.odlc.thumbnail_approved)

    def test_post_delete_old(self):
        """Old image deleted when new doesn't overwrite."""
        self.upload_image('A.jpg')

        t = Odlc.objects.get(pk=self.odlc_id)
        jpg_path = t.thumbnail.path
        self.assertTrue(os.path.exists(jpg_path))

        self.upload_image('A.png', content_type='image/png')
        self.assertFalse(os.path.exists(jpg_path))

    def test_delete(self):
        """Image deleted on DELETE"""
        self.upload_image('A.jpg')

        t = Odlc.objects.get(pk=self.odlc_id)
        jpg_path = t.thumbnail.path
        self.assertTrue(os.path.exists(jpg_path))

        response = self.client.delete(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(200, response.status_code)

        self.assertFalse(os.path.exists(jpg_path))

    def test_get_after_delete(self):
        """GET returns 404 after DELETE"""
        self.upload_image('A.jpg')

        response = self.client.delete(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(200, response.status_code)

        response = self.client.get(odlcs_id_image_url(args=[self.odlc_id]))
        self.assertEqual(404, response.status_code)


class TestOdlcsAdminReviewNotAdmin(TestOdlcsCommon):
    """Tests admin review when not logged in as admin."""
    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        response = self.client.get(odlcs_review_url)
        self.assertEqual(403, response.status_code)

        response = self.client.put(odlcs_review_id_url(args=[1]))
        self.assertEqual(403, response.status_code)

    def test_not_admin(self):
        """Unauthenticated requests should fail."""
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.client.force_login(self.user)

        response = self.client.get(odlcs_review_url)
        self.assertEqual(403, response.status_code)

        response = self.client.put(odlcs_review_id_url(args=[1]))
        self.assertEqual(403, response.status_code)


class TestOdlcsAdminReview(TestOdlcsCommon):
    """Tests GET/PUT admin review of odlcs."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestOdlcsAdminReview, self).setUp()
        self.user = User.objects.create_superuser('testuser',
                                                  'testemail@x.com',
                                                  'testpass')
        self.team = User.objects.create_user('testuser2', 'testemail@x.com',
                                             'testpass')
        self.client.force_login(self.user)

    def test_get_none(self):
        """Test GET when there are no odlcs."""
        response = self.client.get(odlcs_review_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.content))

    def test_get_without_thumbnail(self):
        """Test GET when there are odlcs without thumbnail."""
        odlc = Odlc(mission=self.mission,
                    user=self.team,
                    odlc_type=interop_api_pb2.Odlc.STANDARD)
        odlc.save()

        response = self.client.get(odlcs_review_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(0, len(data))

    def test_get(self):
        """Test GET when there are odlcs."""
        odlc = Odlc(mission=self.mission,
                    user=self.team,
                    odlc_type=interop_api_pb2.Odlc.STANDARD)
        odlc.save()

        with open(test_image('A.jpg'), 'rb') as f:
            odlc.thumbnail.save('%d.%s' % (odlc.pk, 'jpg'), ImageFile(f))
        odlc.save()

        response = self.client.get(odlcs_review_url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertIn('odlc', data[0])
        self.assertIn('type', data[0]['odlc'])
        self.assertEqual('STANDARD', data[0]['odlc']['type'])

    def test_put_review_no_approved(self):
        """Test PUT review with no approved field."""
        odlc = Odlc(mission=self.mission,
                    user=self.team,
                    odlc_type=interop_api_pb2.Odlc.STANDARD)
        odlc.save()

        response = self.client.put(odlcs_review_id_url(args=[odlc.pk]))
        self.assertEqual(400, response.status_code)

    def test_put_invalid_pk(self):
        """Test PUT reivew with invalid pk."""
        response = self.client.put(odlcs_review_id_url(args=[1]),
                                   data=json.dumps({
                                       'thumbnailApproved': True,
                                       'descriptionApproved': True,
                                   }))
        self.assertEqual(404, response.status_code)

    def test_put_review(self):
        """Test PUT review is saved."""
        odlc = Odlc(mission=self.mission,
                    user=self.team,
                    odlc_type=interop_api_pb2.Odlc.STANDARD)
        odlc.save()

        response = self.client.put(odlcs_review_id_url(args=[odlc.pk]),
                                   data=json.dumps({
                                       'thumbnailApproved': True,
                                       'descriptionApproved': True,
                                   }))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertIn('odlc', data)
        self.assertIn('id', data['odlc'])
        self.assertEqual(odlc.pk, data['odlc']['id'])
        self.assertIn('thumbnailApproved', data)
        self.assertTrue(data['thumbnailApproved'])
        self.assertTrue(data['descriptionApproved'])

        odlc.refresh_from_db()
        self.assertTrue(odlc.thumbnail_approved)
        self.assertTrue(odlc.description_approved)
