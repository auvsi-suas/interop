import datetime
from collections import namedtuple
from auvsi_suas.models.time_period import TimePeriod
from django.test import TestCase
from django.utils import timezone

# Sample event class to test TimePeriod with.
Event = namedtuple('Event', ['timestamp', 'start'])


class TestTimePeriod(TestCase):
    """Tests the TimePeriod object."""

    def setUp(self):
        self.is_start_func = lambda x: x.start
        self.is_end_func = lambda x: not x.start

    def test_from_events(self):
        """Tests from_events()."""
        # No periods.
        events = []
        expected = []
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))
        # Standard period.
        events = [Event(0, True), Event(1, False)]
        expected = [TimePeriod(0, 1)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))
        # Multiple periods.
        events = [Event(0, True), Event(1, False), Event(2, True),
                  Event(3, False)]
        expected = [TimePeriod(0, 1), TimePeriod(2, 3)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))

    def test_from_events_invalid(self):
        """Tests from_events() with invalid situations."""
        # No start.
        events = [Event(0, False)]
        expected = [TimePeriod(None, 0)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))
        # No end.
        events = [Event(0, True)]
        expected = [TimePeriod(0, None)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))
        # Multiple start.
        events = [Event(0, True), Event(1, True), Event(2, False)]
        expected = [TimePeriod(0, 2)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))
        # Multiple end.
        events = [Event(0, True), Event(1, False), Event(2, False)]
        expected = [TimePeriod(0, 1)]
        self.assertEqual(expected,
                         TimePeriod.from_events(events, self.is_start_func,
                                                self.is_end_func))

    def test_eq(self):
        """Tests TimePeriod equality."""
        # Self equality
        a = TimePeriod()
        self.assertEqual(a, a)

        # Two None objects
        a = TimePeriod()
        b = TimePeriod()
        self.assertEqual(a, b)

        # Same start (and end)
        a = TimePeriod(start=timezone.now())
        b = TimePeriod(start=a.start)
        self.assertEqual(a, b)

        # Same start, different end
        a = TimePeriod(start=timezone.now())
        b = TimePeriod(start=a.start, end=timezone.now())
        self.assertNotEqual(a, b)

        # Different start, same end
        a = TimePeriod(start=timezone.now(), end=timezone.now())
        b = TimePeriod(start=timezone.now(), end=a.end)
        self.assertNotEqual(a, b)

        # Different start, different end
        a = TimePeriod(start=timezone.now(), end=timezone.now())
        b = TimePeriod(start=timezone.now(), end=timezone.now())
        self.assertNotEqual(a, b)

    def test_within_standard(self):
        """Tests the within method with defined start and end."""
        t = TimePeriod(start=datetime.datetime(2000, 1, 1),
                       end=datetime.datetime(2001, 1, 1))

        # Clearly within
        self.assertTrue(t.within(datetime.datetime(2000, 6, 1)))

        # Inclusive start
        self.assertTrue(t.within(datetime.datetime(2000, 1, 1)))

        # Inclusive end
        self.assertTrue(t.within(datetime.datetime(2001, 1, 1)))

        # Not within below
        self.assertFalse(t.within(datetime.datetime(1999, 1, 1)))

        # Not within above
        self.assertFalse(t.within(datetime.datetime(2002, 1, 1)))

    def test_within_no_start(self):
        """Tests the within method with defined end and no start."""
        t = TimePeriod(end=datetime.datetime(2001, 1, 1))

        # Less than end
        self.assertTrue(t.within(datetime.datetime(2000, 6, 1)))

        # Inclusive end
        self.assertTrue(t.within(datetime.datetime(2001, 1, 1)))

        # Way below
        self.assertTrue(t.within(datetime.datetime(1999, 1, 1)))

        # Not within above
        self.assertFalse(t.within(datetime.datetime(2002, 1, 1)))

    def test_within_no_end(self):
        """Tests the within method with defined start and no end."""
        t = TimePeriod(start=datetime.datetime(2000, 1, 1))

        # Greater than start
        self.assertTrue(t.within(datetime.datetime(2000, 6, 1)))

        # Inclusive start
        self.assertTrue(t.within(datetime.datetime(2000, 1, 1)))

        # Not within below
        self.assertFalse(t.within(datetime.datetime(1999, 1, 1)))

        # Way above
        self.assertTrue(t.within(datetime.datetime(2002, 1, 1)))

    def test_duration_infinite(self):
        """Tests the duration with infinite value (no endpoint)."""
        t = TimePeriod(start=datetime.datetime(2000, 1, 1))
        self.assertIsNone(t.duration())
        t = TimePeriod(end=datetime.datetime(2000, 1, 1))
        self.assertIsNone(t.duration())

    def test_duration_finite(self):
        """Tests the duration with endpoints and finite time."""
        t = TimePeriod(start=datetime.datetime(2000, 1, 1),
                       end=datetime.datetime(2000, 1, 2))
        self.assertEqual(datetime.timedelta(days=1), t.duration())
