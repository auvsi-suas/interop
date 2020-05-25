"""Tests for the mission_config module."""

from auvsi_suas.models import test_utils
from auvsi_suas.models.mission_config import MissionConfig
from django.contrib.auth.models import User
from django.test import TestCase


class TestMissionConfigModelSampleMission(TestCase):
    def setUp(self):
        superuser = User.objects.create_superuser(username='testadmin',
                                                  password='testpass',
                                                  email='test@test.com')
        superuser.save()
        test_utils.create_sample_mission(superuser)

    def test_str(self):
        for mission in MissionConfig.objects.all():
            self.assertNotEqual(str(mission), '')

    def test_clean(self):
        """Test model validation."""
        for mission in MissionConfig.objects.all():
            mission.full_clean()
