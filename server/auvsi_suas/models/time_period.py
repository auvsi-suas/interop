import logging

logger = logging.getLogger(__name__)


class TimePeriod(object):
    """
    Describe a continuous period of time.
    A value of None indicates infinity. Both start and end are inclusive.
    """
    @classmethod
    def from_events(cls, events, is_start_func, is_end_func):
        """Gets a list of time periods from a list of events.

        Args:
            events: List of events which have a timestamp property.
            is_start_func: Lambda which returns whether an event is the start
                of a period.
            is_end_func: Lambda which returns whether an event is the end
                of a period.
        Returns:
            A list of time periods.
        """
        if not events:
            return []

        periods = []
        # Handle end with no start, use None as infinity.
        if events and is_end_func(events[0]):
            periods.append(TimePeriod(None, events[0].timestamp))
        # Detect transitions from start->end and end->start.
        start_time = None
        started = False
        for event in events:
            if not started and is_start_func(event):
                start_time = event.timestamp
                started = True
            elif started and is_end_func(event):
                periods.append(TimePeriod(start_time, event.timestamp))
                started = False
        # Handle start with no end, use None as infinity.
        if started:
            periods.append(TimePeriod(start_time, None))

        return periods

    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def __eq__(self, other):
        """Two TimePeriods are equal if their attributes are equal."""
        if type(other) == type(self):
            return self.__dict__ == other.__dict__
        return False

    def within(self, time):
        """Returns true if time is within the TimePeriod."""
        return (self.start is None or time >= self.start) and \
                (self.end is None or time <= self.end)

    def duration(self):
        """Returns time duration as datetime.TimeDelta, or None if infinite."""
        if self.start is None or self.end is None:
            return None
        return self.end - self.start
