"""Tests for the access_log module."""

import datetime
from auvsi_suas.models.access_log import AccessLogMixin
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.time_period import TimePeriod
from auvsi_suas.models.uas_telemetry import UasTelemetry
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

# We use UasTelemetry as a concrete version of AccessLogMixin, which is actually
# testable.


class TestSanity(TestCase):
    """Make sure UasTelemetry is a canonical AccessLogMixin."""
    def test_uas_telemetry_access_log(self):
        self.assertTrue(issubclass(UasTelemetry, AccessLogMixin))


class TestAccessLogMixinCommon(TestCase):
    """Common code for AccessLogMixin model tests."""
    def setUp(self):
        """Sets up the tests."""
        self.user1 = User.objects.create_user('user1', 'email@example.com',
                                              'pass')

        self.user2 = User.objects.create_user('user2', 'email@example.com',
                                              'pass')

        self.year2000 = datetime.datetime(2000, 1, 1, tzinfo=timezone.utc)
        self.year2001 = datetime.datetime(2001, 1, 1, tzinfo=timezone.utc)
        self.year2002 = datetime.datetime(2002, 1, 1, tzinfo=timezone.utc)
        self.year2003 = datetime.datetime(2003, 1, 1, tzinfo=timezone.utc)
        self.year2004 = datetime.datetime(2004, 1, 1, tzinfo=timezone.utc)

    def create_logs(self, user, num=10, start=None, delta=None):
        if start is None:
            start = timezone.now()
        if delta is None:
            delta = datetime.timedelta(seconds=1)

        logs = []

        for i in range(num):
            log = UasTelemetry(user=user,
                               latitude=0,
                               longitude=0,
                               altitude_msl=0,
                               uas_heading=0.0)
            log.save()
            log.timestamp = start + i * delta
            log.save()
            logs.append(log)

        return logs


class TestAccessLogMixinBasic(TestAccessLogMixinCommon):
    """Tests the AccessLogMixin model basic functionality."""
    def test_no_data(self):
        self.assertEqual(None, UasTelemetry.last_for_user(self.user1))
        self.assertEqual(0, len(UasTelemetry.by_user(self.user1)))

        # Empty time priod.
        self.assertSequenceEqual([],
                                 UasTelemetry.by_time_period(self.user1, []))
        self.assertTupleEqual((None, None), UasTelemetry.rates(self.user1, []))

        start = timezone.now()
        delta = datetime.timedelta(seconds=10)

        # Time periods which calculate a rate.
        time_period_sets = [
            [TimePeriod(start, start + delta)],
            [
                TimePeriod(start, start + delta),
                TimePeriod(start + delta, start + delta * 2)
            ],
        ]
        for time_periods in time_period_sets:
            for logs in UasTelemetry.by_time_period(self.user1, time_periods):
                self.assertEqual(0, len(logs))
            self.assertTupleEqual(
                (delta.total_seconds(), delta.total_seconds()),
                UasTelemetry.rates(self.user1, time_periods))

        # Open time periods which can't calculate a rate.
        time_period_sets = [
            [],
            [TimePeriod(None, start)],
            [TimePeriod(start + delta, None)],
            [
                TimePeriod(None, start),
                TimePeriod(start, start + delta),
                TimePeriod(start + delta, None)
            ],
        ]

        for time_periods in time_period_sets:
            for logs in UasTelemetry.by_time_period(self.user1, time_periods):
                self.assertEqual(0, len(logs))
            self.assertTupleEqual((None, None),
                                  UasTelemetry.rates(self.user1, time_periods))

    def test_basic_access(self):
        start = timezone.now() - datetime.timedelta(seconds=10)
        logs = self.create_logs(self.user1, start=start)

        log = UasTelemetry.last_for_user(self.user1)
        self.assertEqual(logs[-1], log)

        results = UasTelemetry.by_user(self.user1)
        self.assertSequenceEqual(logs, results)

    def test_multi_user(self):
        # Intersperse logs from two users
        logs = []
        for _ in range(10):
            logs += self.create_logs(self.user1, num=1)
            self.create_logs(self.user2, num=1)

        log = UasTelemetry.last_for_user(self.user1)
        self.assertEqual(logs[-1], log)

        results = UasTelemetry.by_user(self.user1)
        self.assertSequenceEqual(logs, results)

    def test_by_user_time_restrict(self):
        start = timezone.now()
        delta = datetime.timedelta(seconds=1)
        expect_logs = self.create_logs(self.user1,
                                       num=10,
                                       start=start,
                                       delta=delta)

        logs = UasTelemetry.by_user(self.user1,
                                    start_time=start,
                                    end_time=start + delta * 10)
        self.assertSequenceEqual(expect_logs, logs)

        logs = UasTelemetry.by_user(self.user1, start_time=start + delta * 11)
        self.assertSequenceEqual([], logs)
        logs = UasTelemetry.by_user(self.user1, end_time=start)
        self.assertSequenceEqual([], logs)

    def test_last_for_user_time_restrict(self):
        start = timezone.now()
        delta = datetime.timedelta(seconds=1)
        logs = self.create_logs(self.user1, num=10, start=start, delta=delta)

        log = UasTelemetry.last_for_user(self.user1,
                                         start_time=start,
                                         end_time=start + delta * 3)
        self.assertEqual(logs[2], log)

        log = UasTelemetry.last_for_user(self.user1,
                                         start_time=start + delta * 11)
        self.assertIsNone(log)
        log = UasTelemetry.last_for_user(self.user1, end_time=start - delta)
        self.assertIsNone(log)


class TestAccessLogMixinByTimePeriod(TestAccessLogMixinCommon):
    """Test AccessLogMixin.by_time_period()"""
    def setUp(self):
        super(TestAccessLogMixinByTimePeriod, self).setUp()

        self.year2000_logs = self.create_logs(self.user1, start=self.year2000)
        self.year2003_logs = self.create_logs(self.user1, start=self.year2003)
        self.logs = self.year2000_logs + self.year2003_logs

    def to_lists(self, results):
        """Convert a list of QuerySet results to a list of lists."""
        return [list(r) for r in results]

    def test_single_period(self):
        """Single set of logs accessible."""
        results = UasTelemetry.by_time_period(
            self.user1, [TimePeriod(self.year2000, self.year2001)])

        self.assertSequenceEqual([self.year2000_logs], self.to_lists(results))

    def test_full_range(self):
        """All logs from (-inf, inf)."""
        results = UasTelemetry.by_time_period(self.user1,
                                              [TimePeriod(None, None)])

        self.assertSequenceEqual([self.logs], self.to_lists(results))

    def test_both_periods(self):
        """Both sets of logs, accesses individually."""
        results = UasTelemetry.by_time_period(self.user1, [
            TimePeriod(self.year2000, self.year2001),
            TimePeriod(self.year2003, self.year2004),
        ])

        self.assertSequenceEqual([self.year2000_logs, self.year2003_logs],
                                 self.to_lists(results))

    def test_non_intersecting_period(self):
        """No logs matched."""
        results = UasTelemetry.by_time_period(self.user1, [
            TimePeriod(self.year2001, self.year2002),
        ])

        self.assertSequenceEqual([[]], self.to_lists(results))

    def test_one_intersecting_period(self):
        """Only one period matches logs."""
        results = UasTelemetry.by_time_period(self.user1, [
            TimePeriod(self.year2001, self.year2002),
            TimePeriod(self.year2003, self.year2004),
        ])

        self.assertSequenceEqual([[], self.year2003_logs],
                                 self.to_lists(results))

    def test_open_start(self):
        """Logs (-inf, 2001)"""
        results = UasTelemetry.by_time_period(self.user1, [
            TimePeriod(None, self.year2001),
        ])

        self.assertSequenceEqual([self.year2000_logs], self.to_lists(results))

    def test_open_end(self):
        """Logs (2003, inf)"""
        results = UasTelemetry.by_time_period(self.user1, [
            TimePeriod(self.year2003, None),
        ])

        self.assertSequenceEqual([self.year2003_logs], self.to_lists(results))


class TestAccessLogMixinRates(TestAccessLogMixinCommon):
    """Test AccessLogMixin.rates()"""
    def consistent_period(self, logs, delta):
        # rates() uses time between beginning/end of the period
        # and the first/last log to compute rates, so to get constant rates,
        # the period must begin and end delta seconds before/after the logs.
        return TimePeriod(logs[0].timestamp - delta,
                          logs[-1].timestamp + delta)

    def test_no_logs(self):
        """Test behavior when no logs are present."""
        delta = datetime.timedelta(seconds=10)
        self.assertSequenceEqual(
            (10, 10),
            UasTelemetry.rates(
                self.user1,
                [TimePeriod(self.year2000, self.year2000 + delta)]))

    def test_constant_rate(self):
        """Rates computed correctly."""
        delta = datetime.timedelta(seconds=1)

        logs = self.create_logs(self.user1, delta=delta)
        period = self.consistent_period(logs, delta)

        rates = UasTelemetry.rates(self.user1, [period])

        self.assertSequenceEqual((1, 1), rates)

    def test_non_constant_rate(self):
        """Rates computed correctly when non-constant."""
        delta = datetime.timedelta(seconds=1)

        start = timezone.now()
        self.create_logs(self.user1, num=10, start=start, delta=delta)
        self.create_logs(self.user1,
                         num=10,
                         start=start + 10 * delta,
                         delta=2 * delta)
        period = TimePeriod(start - delta,
                            start + 10 * delta + 10 * (2 * delta))
        rates = UasTelemetry.rates(self.user1, [period])

        self.assertSequenceEqual((2, (1.0 * 11 + 2.0 * 10) / (11 + 10)), rates)

    def test_delayed_start_early_end_logs(self):
        """Rates computed consider time before and after log sequence."""
        delta = datetime.timedelta(seconds=1)

        logs = self.create_logs(self.user1, delta=delta)
        period = self.consistent_period(logs, delta * 2)

        rates = UasTelemetry.rates(self.user1, [period])

        self.assertSequenceEqual((2, (1.0 * 9 + 2.0 * 2) / (9 + 2)), rates)

    def test_provided_logs(self):
        """Rates computed with provided logs only."""
        delta = datetime.timedelta(seconds=1)

        used_logs = self.create_logs(self.user1, delta=delta)
        unused_logs = self.create_logs(self.user1, delta=delta)
        period = self.consistent_period(used_logs, delta)

        rates = UasTelemetry.rates(self.user1, [period],
                                   time_period_logs=[used_logs])

        self.assertSequenceEqual((1, 1), rates)

    def test_infinite_period(self):
        """Can't calculate a rate for an infinite (unbounded) period."""
        delta = datetime.timedelta(seconds=1)
        logs = self.create_logs(self.user1, delta=delta)
        period = TimePeriod(None, None)

        self.assertSequenceEqual((None, None),
                                 UasTelemetry.rates(self.user1, [period]))

    def test_multiple_periods(self):
        """Multiple periods are combined without introducing errors."""
        delta = datetime.timedelta(seconds=1)

        logs = [
            self.create_logs(self.user1, start=self.year2000, delta=delta),
            self.create_logs(self.user1, start=self.year2001, delta=delta),
        ]

        periods = [self.consistent_period(l, delta) for l in logs]

        rates = UasTelemetry.rates(self.user1, periods)

        self.assertSequenceEqual((1, 1), rates)

    def test_different_deltas(self):
        """Sets of logs are combined for overall rates."""
        delta = datetime.timedelta(seconds=1)

        logs = [
            self.create_logs(self.user1,
                             num=1000,
                             start=self.year2000,
                             delta=delta),
            self.create_logs(self.user1,
                             num=1000,
                             start=self.year2001,
                             delta=delta / 2),
        ]

        periods = [self.consistent_period(l, delta) for l in logs]

        rates = UasTelemetry.rates(self.user1, periods)

        self.assertAlmostEqual(1.0, rates[0])  # max
        self.assertAlmostEqual(0.75, rates[1], delta=0.001)  # avg
