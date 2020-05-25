"""Model for an access log."""

import functools
import logging
import numpy as np
from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class AccessLogMixin(models.Model):
    """Base class which logs access of information."""
    # The user which accessed the data.
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             db_index=True,
                             on_delete=models.CASCADE)
    # Timestamp of the access.
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True
        index_together = (('user', 'timestamp'), )

    def __init__(self, *args, **kwargs):
        super(AccessLogMixin, self).__init__(*args, **kwargs)
        if self.timestamp is None:
            self.timestamp = timezone.now()

    @classmethod
    def by_user(cls, user, start_time=None, end_time=None):
        """Gets the time-sorted list of access log for the given user.

        Args:
            user: The user to get the access log for.
            start_time: Optional. Inclusive start time.
            end_time: Optional. Exclusive end time.
        Returns:
            A list of access log objects for the given user sorted by timestamp.
        """
        query = cls.objects.filter(user_id=user.pk)
        if start_time:
            query = query.filter(timestamp__gte=start_time)
        if end_time:
            query = query.filter(timestamp__lt=end_time)
        return query.order_by('timestamp')

    @classmethod
    def last_for_user(cls, user, start_time=None, end_time=None):
        """Gets the last access log for the user.

        Args:
            user: The user to get the access log for.
            start_time: Optional. Inclusive start time.
            end_time: Optional. Exclusive end time.
        Returns:
            The last access log for the user.
        """
        return cls.by_user(user, start_time, end_time).last()

    @classmethod
    def by_time_period(cls, user, time_periods):
        """Gets a list of time-sorted lists of access logs for each time period.

        The method returns the full sets of AccessLogMixins for each TimePeriod. If
        overlapping TimePeriods are provided, the results may contain duplicate
        logs.

        Args:
            user: The user to get the access log for.
            time_periods: A list of TimePeriod objects.
        Returns:
            A list of AccessLogMixin lists, where each AccessLogMixin list contains all
            AccessLogMixins corresponding to the related TimePeriod.
        """
        return [cls.by_user(user, p.start, p.end) for p in time_periods]

    @classmethod
    def rates(cls, user, time_periods, time_period_logs=None):
        """Gets the access log rates.

        Args:
            user: The user to get the access log rates for.
            time_periods: A list of TimePeriod objects. Note: to avoid
                computing rates with duplicate logs, ensure that all
                time periods are non-overlapping.
            time_period_logs: Optional. A sequence of AccessLogMixin sequences,
                where each AccessLogMixin sequence contains all AccessLogMixins
                corresponding to the related TimePeriod. If None, will obtain
                by calling by_time_period().
        Returns:
            A (max, avg) tuple. The max is the max time between logs, and avg
            is the avg time between logs.
            """
        # Check that time periods were provided.
        if not time_periods:
            return (None, None)

        # Check that all time periods are closed.
        for time_period in time_periods:
            if time_period.duration() is None:
                return (None, None)

        # If logs were not provided, obtain.
        if not time_period_logs:
            time_period_logs = cls.by_time_period(user, time_periods)

        # Utility generator for time durations.
        def time_between_logs(time_periods, time_period_logs):
            for ix, period in enumerate(time_periods):
                prev_time = period.start
                for log in time_period_logs[ix]:
                    yield (log.timestamp - prev_time).total_seconds()
                    prev_time = log.timestamp
                yield (period.end - prev_time).total_seconds()

        # Calculate max, sum, count for time durations.
        (m, s, c) = functools.reduce(
            lambda r, d: (max(r[0], d), r[1] + d, r[2] + 1),
            time_between_logs(time_periods, time_period_logs), (0.0, 0.0, 0))
        # Convert to max and average.
        return (m, s / c)
