"""Tests for the takeoff_or_landing_event module."""

import datetime
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.time_period import TimePeriod
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.models.access_log_test import TestAccessLogMixinCommon


class TestTakeoffOrLandingEventModel(TestAccessLogMixinCommon):
    """Tests the TakeoffOrLandingEvent model."""
    def setUp(self):
        super(TestTakeoffOrLandingEventModel, self).setUp()

        # Mission
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        apos = AerialPosition()
        apos.latitude = 10
        apos.longitude = 100
        apos.altitude_msl = 1000
        apos.save()
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

        self.ten_minutes = datetime.timedelta(minutes=10)

    def create_event(self, time, uas_in_air, mission=None):
        """Create a TakeoffOrLandingEvent for test user."""
        if mission is None:
            mission = self.mission
        event = TakeoffOrLandingEvent(user=self.user1,
                                      mission=mission,
                                      uas_in_air=uas_in_air)
        event.save()
        event.timestamp = time
        event.save()
        return event

    def evaluate_periods(self, expected):
        """Check actual periods against expected."""
        periods = TakeoffOrLandingEvent.flights(self.mission, self.user1)

        self.assertSequenceEqual(expected, periods)

    def test_basic_flight_period(self):
        """Single flight reported as period."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + self.ten_minutes),
        ])

    def test_flight_period_missing_takeoff(self):
        """Missing takeoff reported as None."""
        self.create_event(self.year2000, False)

        self.evaluate_periods([
            TimePeriod(None, self.year2000),
        ])  # yapf: disable

    def test_flight_period_missing_landing(self):
        """Missing landing reported as None."""
        self.create_event(self.year2000, True)

        self.evaluate_periods([
            TimePeriod(self.year2000, None),
        ])  # yapf: disable

    def test_flight_period_multiple_flights(self):
        """Multiple flight reported together."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.create_event(self.year2001, True)
        self.create_event(self.year2001 + self.ten_minutes, False)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + self.ten_minutes),
            TimePeriod(self.year2001, self.year2001 + self.ten_minutes),
        ])

    def test_flight_period_multiple_flights_order(self):
        """Multiple flights listed in chronological order."""
        self.create_event(self.year2001, True)
        self.create_event(self.year2001 + self.ten_minutes, False)

        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + self.ten_minutes),
            TimePeriod(self.year2001, self.year2001 + self.ten_minutes),
        ])

    def test_flight_period_specific_mission(self):
        """Tests that it only includes flights for specified mission."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.create_event(self.year2001, True, self.mission2)
        self.create_event(self.year2001 + self.ten_minutes, False,
                          self.mission2)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + self.ten_minutes),
        ])

    def test_flight_period_missing_multiple(self):
        """Multiple flight can be missing details."""
        # Forgot takeoff
        self.create_event(self.year2000, False)

        # Normal
        self.create_event(self.year2001, True)
        self.create_event(self.year2001 + self.ten_minutes, False)

        # Forgot landing
        self.create_event(self.year2002, True)

        self.evaluate_periods([
            TimePeriod(None, self.year2000),
            TimePeriod(self.year2001, self.year2001 + self.ten_minutes),
            TimePeriod(self.year2002, None),
        ])

    def test_flight_period_multiple_landing(self):
        """Double landing ignored"""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        # Land again? Ignored
        self.create_event(self.year2000 + 2 * self.ten_minutes, False)

        self.create_event(self.year2001, True)
        self.create_event(self.year2001 + self.ten_minutes, False)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + self.ten_minutes),
            TimePeriod(self.year2001, self.year2001 + self.ten_minutes),
        ])

    def test_flight_period_multiple_takeoff(self):
        """Double takeoff ignored."""
        self.create_event(self.year2000, True)
        # Take off again? Ignored
        self.create_event(self.year2000 + self.ten_minutes, True)
        # Land
        self.create_event(self.year2000 + 2 * self.ten_minutes, False)

        self.create_event(self.year2001, True)
        self.create_event(self.year2001 + self.ten_minutes, False)

        self.evaluate_periods([
            TimePeriod(self.year2000, self.year2000 + 2 * self.ten_minutes),
            TimePeriod(self.year2001, self.year2001 + self.ten_minutes),
        ])

    def test_user_in_air_no_logs(self):
        """Not in-air without logs."""
        self.assertFalse(TakeoffOrLandingEvent.user_in_air(self.user1))

    def test_user_in_air_before_landing(self):
        """In-air before landing."""
        self.create_event(self.year2000, True)

        self.assertTrue(TakeoffOrLandingEvent.user_in_air(self.user1))

    def test_user_in_air_after_landing(self):
        """Not in-air after landing."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.assertFalse(TakeoffOrLandingEvent.user_in_air(self.user1))

    def test_user_in_air_second_flight(self):
        """In-air during second flight."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + self.ten_minutes, False)

        self.create_event(self.year2001, True)

        self.assertTrue(TakeoffOrLandingEvent.user_in_air(self.user1))

    def test_user_in_air_time(self):
        """In-air base time check."""
        self.create_event(self.year2000, True)
        self.create_event(self.year2000 + 2 * self.ten_minutes, False)

        time = self.year2000 + self.ten_minutes

        self.assertTrue(
            TakeoffOrLandingEvent.user_in_air(self.user1, time=time))
