"""Tests for the map module."""

import functools
import os.path
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.map import Map
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.proto import interop_admin_api_pb2
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.test import TestCase
from django.urls import reverse

map_url = functools.partial(reverse, 'auvsi_suas:map')


class TestMapCommon(TestCase):
    """Common functionality for map tests."""
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
        self.mission.map_center_pos = pos
        self.mission.map_height_ft = 1
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
        self.mission2.map_center_pos = pos
        self.mission2.map_height_ft = 1
        self.mission2.air_drop_pos = pos
        self.mission2.ugv_drive_pos = pos
        self.mission2.save()
        self.mission2.mission_waypoints.add(wpt)
        self.mission2.search_grid_points.add(wpt)
        self.mission2.save()

        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')

    def filled_url(self):
        """Returns a filled map URL."""
        return map_url(args=[self.mission.pk, self.user.username])


class TestMapLoggedOut(TestMapCommon):
    """Tests logged out map."""
    def test_not_authenticated(self):
        """Unauthenticated requests should fail."""
        response = self.client.put(self.filled_url(),
                                   data='foobar',
                                   content_type='text/plain')
        self.assertEqual(403, response.status_code)

        response = self.client.get(self.filled_url())
        self.assertEqual(403, response.status_code)

        response = self.client.delete(self.filled_url())
        self.assertEqual(403, response.status_code)


def test_image(name):
    """Compute path of test image"""
    return os.path.join(settings.BASE_DIR, 'auvsi_suas/testdata', name)


class TestMapImage(TestMapCommon):
    """Tests GET/PUT/DELETE map image."""
    def setUp(self):
        """Creates user and logs in."""
        super(TestMapImage, self).setUp()
        self.client.force_login(self.user)

    def test_get_no_image(self):
        """404 when GET image before upload."""
        response = self.client.get(self.filled_url())
        self.assertEqual(404, response.status_code)

    def test_delete_no_image(self):
        """404 when DELETE image before upload."""
        response = self.client.delete(self.filled_url())
        self.assertEqual(404, response.status_code)

    def test_get_other_user(self):
        """Test GETting a thumbnail owned by a different user."""
        user2 = User.objects.create_user('testuser2', 'testemail@x.com',
                                         'testpass')
        response = self.client.get(
            map_url(args=[self.mission.pk, user2.username]))
        self.assertEqual(403, response.status_code)

    def test_put_bad_image(self):
        """Try to upload bad image"""
        response = self.client.put(self.filled_url(),
                                   data='Hahaha',
                                   content_type='image/jpeg')
        self.assertEqual(400, response.status_code)

    def upload_image(self, name, content_type='image/jpeg'):
        """Upload image, assert that it worked"""
        # Read image to upload.
        data = None
        with open(test_image(name), 'rb') as f:
            data = f.read()

        # Upload image.
        response = self.client.put(self.filled_url(),
                                   data=data,
                                   content_type=content_type)
        self.assertEqual(200, response.status_code)

        # Validate can retrieve image with uploaded contents.
        response = self.client.get(self.filled_url())
        self.assertEqual(200, response.status_code)
        resp_data = b''.join(response.streaming_content)
        self.assertEqual(data, resp_data)

    def test_put_jpg(self):
        """Successfully upload jpg"""
        self.upload_image('S.jpg')

    def test_put_png(self):
        """Successfully upload png"""
        self.upload_image('A.png', content_type='image/png')

    def test_put_gif(self):
        """GIF upload not allowed"""
        with open(test_image('A.gif'), 'rb') as f:
            response = self.client.put(self.filled_url(),
                                       data=f.read(),
                                       content_type='image/gif')
            self.assertEqual(400, response.status_code)

    def test_get_image(self):
        """Successfully GET uploaded image"""
        self.upload_image('S.jpg')

        response = self.client.get(self.filled_url())
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

    def test_update_invalidates_review(self):
        """Test that update invalidates review field(s)."""
        # Upload an image.
        self.upload_image('A.jpg')

        # Judge reviews and sets the quality.
        m = Map.objects.get(mission_id=self.mission.pk, user=self.user)
        m.quality = interop_admin_api_pb2.MapEvaluation.MapQuality.MEDIUM
        m.save()

        # User overwrites wiht a new image, judge review cleared.
        self.upload_image('A.jpg')
        m.refresh_from_db()
        self.assertIsNone(m.quality)

    def test_put_delete_old(self):
        """Old image deleted when new overwrites."""
        self.upload_image('A.jpg')
        m = Map.objects.get(mission_id=self.mission.pk, user=self.user)
        path = m.uploaded_map.path
        self.assertTrue(os.path.exists(path))

        self.upload_image('A.png', content_type='image/png')
        self.assertFalse(os.path.exists(path))

    def test_delete(self):
        """Image deleted on DELETE"""
        self.upload_image('A.jpg')
        m = Map.objects.get(mission_id=self.mission.pk, user=self.user)
        path = m.uploaded_map.path
        self.assertTrue(os.path.exists(path))

        response = self.client.delete(self.filled_url())
        self.assertEqual(200, response.status_code)

        self.assertFalse(os.path.exists(path))

    def test_get_after_delete(self):
        """GET returns 404 after DELETE"""
        self.upload_image('A.jpg')

        response = self.client.delete(self.filled_url())
        self.assertEqual(200, response.status_code)

        response = self.client.get(self.filled_url())
        self.assertEqual(404, response.status_code)
