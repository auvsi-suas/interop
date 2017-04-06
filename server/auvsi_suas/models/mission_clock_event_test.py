"""Tests for the mission_clock_event module."""

import datetime
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.time_period import TimePeriod
from auvsi_suas.models.access_log_test import TestAccessLogCommon
from django.utils import timezone


class TestMissionClockEventModel(TestAccessLogCommon):
    """Tests the MissionClockEvent model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        log = MissionClockEvent(user=self.user1,
                                team_on_clock=True,
                                team_on_timeout=False)
        log.save()
        self.assertIsNotNone(log.__unicode__())

    def test_user_on_clock(self):
        """Tests the user_on_clock method."""
        log = MissionClockEvent(user=self.user1,
                                team_on_clock=False,
                                team_on_timeout=False)
        log.save()
        log = MissionClockEvent(user=self.user2,
                                team_on_clock=True,
                                team_on_timeout=False)
        log.save()

        self.assertFalse(MissionClockEvent.user_on_clock(self.user1))
        self.assertTrue(MissionClockEvent.user_on_clock(self.user2))

    def test_user_on_timeout(self):
        """Tests the user_on_timeout method."""
        log = MissionClockEvent(user=self.user1,
                                team_on_clock=False,
                                team_on_timeout=False)
        log.save()
        log = MissionClockEvent(user=self.user2,
                                team_on_clock=False,
                                team_on_timeout=True)
        log.save()

        self.assertFalse(MissionClockEvent.user_on_timeout(self.user1))
        self.assertTrue(MissionClockEvent.user_on_timeout(self.user2))

    def test_missions(self):
        """Tets the missions()."""
        on_clock = MissionClockEvent(user=self.user1,
                                     team_on_clock=True,
                                     team_on_timeout=False)
        on_clock.save()
        on_clock.timestamp = self.year2000
        on_clock.save()

        on_timeout = MissionClockEvent(user=self.user1,
                                       team_on_clock=False,
                                       team_on_timeout=True)
        on_timeout.save()
        on_timeout.timestamp = self.year2001
        on_timeout.save()

        off_timeout = MissionClockEvent(user=self.user1,
                                        team_on_clock=True,
                                        team_on_timeout=False)
        off_timeout.save()
        off_timeout.timestamp = self.year2002
        off_timeout.save()

        off_clock = MissionClockEvent(user=self.user1,
                                      team_on_clock=False,
                                      team_on_timeout=False)
        off_clock.save()
        off_clock.timestamp = self.year2003
        off_clock.save()

        random_event = MissionClockEvent(user=self.user2,
                                         team_on_clock=True,
                                         team_on_timeout=False)
        random_event.save()

        missions = MissionClockEvent.missions(self.user1)
        self.assertEqual(
            [TimePeriod(self.year2000, self.year2001),
             TimePeriod(self.year2002, self.year2003)], missions)
