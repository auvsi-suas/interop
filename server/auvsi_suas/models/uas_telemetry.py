"""UAS Telemetry model."""

import datetime
import itertools
import logging
from auvsi_suas.models.access_log import AccessLogMixin
from auvsi_suas.models.aerial_position import AerialPositionMixin
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.proto import interop_admin_api_pb2
from collections import defaultdict
from django.contrib import admin
from django.core import validators
from django.db import models

logger = logging.getLogger(__name__)

# Threshold at which telemetry is too close to (0, 0) and likely noise.
BAD_TELEMETRY_THRESHOLD_DEGREES = 0.1
# The incremental step in seconds for an interpolation of telemetry.
TELEMETRY_INTERPOLATION_STEP = datetime.timedelta(seconds=0.1)
# The max time gap between two telemetry to interpolate between.
TELEMETRY_INTERPOLATION_MAX_GAP = datetime.timedelta(seconds=5.0)

# The time window (in seconds) in which a plane cannot be counted as going out
# of bounds multiple times. This prevents noisy input data from recording
# significant more violations than a human observer.
# The max distance for a waypoint to be considered satisfied.
SATISFIED_WAYPOINT_DIST_MAX_FT = 100


class UasTelemetry(AccessLogMixin, AerialPositionMixin):
    """UAS telemetry reported by teams."""

    # The (true north) heading of the UAS in degrees.
    uas_heading = models.FloatField(validators=[
        validators.MinValueValidator(0),
        validators.MaxValueValidator(360),
    ])

    def duplicate(self, other):
        """Determines whether this UasTelemetry is equivalent to another.

        This differs from the Django __eq__() method which simply compares
        primary keys. This method compares the field values.

        Args:
            other: The other log for comparison.
        Returns:
            True if they are equal.
        """
        return (super(UasTelemetry, self).duplicate(other)
                and self.uas_heading == other.uas_heading)

    @classmethod
    def by_user(cls, *args, **kwargs):
        """Gets the time-sorted list of access log for the given user.

        Note: This prefetches the related AerialPosition and GpsPosition
        for each entry.  Thus, any subsequent changes to those entries in
        the database after fetch may not be reflected in the objects.

        Args:
            user: The user to get the access log for.
        Returns:
            A list of access log objects for the given user sorted by timestamp.
        """
        # Almost every user of UasTelemetry.by_user wants to use
        # the related AerialPosition and GpsPosition.  To avoid excessive
        # database queries, we select these values from the database up front.
        return super(UasTelemetry, cls).by_user(*args, **kwargs)

    @classmethod
    def dedupe(cls, logs):
        """Dedupes a set of UAS telemetry logs.

        For every set of sequential telemetry logs that are duplicates, it will
        filter all but the first log. Sensors and autopilots are unlikely to
        provide exactly the same data, even if the system is stationary, so
        logs which have exactly the same values are likely duplicates. Duplicate
        telemetry data is not allowed per the rules, so it is filtered.

        Args:
            logs: A sorted list of UasTelemetry logs.
        Returns:
            A sequence containing the non-duplicate logs in the original list.
        """
        # Check that logs were provided.
        if not logs:
            return logs

        # For each log, compare to previous. If different, add to output.
        prev_log = None
        for log in logs:
            if not prev_log or not prev_log.duplicate(log):
                # New unique log.
                yield log
                prev_log = log

    @classmethod
    def filter_bad(cls, logs):
        """Filters bad telemetry from the list.

        Args:
            logs: A sorted list of UasTelemetry logs.
        Returns:
            A list containing the non-bad logs.
        """
        def _is_good(log):
            # Positions near (0,0) are likely GPS/autopilot noise.
            return max(abs(log.latitude), abs(
                log.longitude)) > BAD_TELEMETRY_THRESHOLD_DEGREES

        return filter(lambda log: _is_good(log), logs)

    @classmethod
    def interpolate(cls,
                    uas_telemetry_logs,
                    step=TELEMETRY_INTERPOLATION_STEP,
                    max_gap=TELEMETRY_INTERPOLATION_MAX_GAP):
        """Interpolates the ordered set of telemetry.

        Args:
            uas_telemetry_logs: The telemetry to interpolate.
            step: The discrete interpolation step in seconds.
            max_gap: The max time between telemetry to interpolate.
        Returns:
            An iterable set of telemetry.
        """
        for ix, log in enumerate(uas_telemetry_logs):
            yield log

            if ix + 1 >= len(uas_telemetry_logs):
                continue
            next_log = uas_telemetry_logs[ix + 1]

            dt = next_log.timestamp - log.timestamp
            if dt > max_gap or dt <= datetime.timedelta(seconds=0):
                continue

            t = log.timestamp + step
            while t < next_log.timestamp:
                n_w = (t - log.timestamp).total_seconds() / dt.total_seconds()
                w = (next_log.timestamp -
                     t).total_seconds() / dt.total_seconds()
                weighted_avg = lambda v, n_v: w * v + n_w * n_v

                telem = UasTelemetry()
                telem.user = log.user
                telem.timestamp = t
                telem.latitude = weighted_avg(log.latitude, next_log.latitude)
                telem.longitude = weighted_avg(log.longitude,
                                               next_log.longitude)
                telem.altitude_msl = weighted_avg(log.altitude_msl,
                                                  next_log.altitude_msl)
                telem.uas_heading = weighted_avg(log.uas_heading,
                                                 next_log.uas_heading)
                yield telem

                t += step

    @classmethod
    def satisfied_waypoints(cls, home_pos, waypoints, uas_telemetry_logs):
        """Determines whether the UAS satisfied the waypoints.

        Waypoints must be satisfied in order. The entire pattern may be
        restarted at any point. The best (most waypoints satisfied) attempt
        will be returned.

        Assumes that waypoints are at least
        SATISFIED_WAYPOINT_DIST_MAX_FT apart.

        Args:
            home_pos: The home position for projections.
            waypoints: A list of waypoints to check against.
            uas_telemetry_logs: A list of UAS Telemetry logs to evaluate.
        Returns:
            A list of auvsi_suas.proto.WaypointEvaluation.
        """
        # Reduce telemetry from telemetry to waypoint hits.
        # This will make future processing more efficient via data reduction.
        # While iterating, compute the best distance seen for feedback.
        best = {}
        hits = []
        for log in cls.interpolate(uas_telemetry_logs):
            for iw, waypoint in enumerate(waypoints):
                dist = log.distance_to(waypoint)
                best[iw] = min(best.get(iw, dist), dist)
                score = max(
                    0,
                    float(SATISFIED_WAYPOINT_DIST_MAX_FT - dist) /
                    SATISFIED_WAYPOINT_DIST_MAX_FT)
                if score > 0:
                    hits.append((iw, dist, score))
        # Remove redundant hits which wouldn't be part of best sequence.
        # This will make future processing more efficient via data reduction.
        hits = [
            max(g, key=lambda x: x[2])
            for _, g in itertools.groupby(hits, lambda x: x[0])
        ]

        # Find highest scoring sequence via dynamic programming.
        # Implement recurrence relation:
        #   S(iw, ih) = s[iw, ih] + max_{k=[0,ih)} S(iw-1, k)
        dp = defaultdict(lambda: defaultdict(lambda: (0, None, None)))
        highest_total = None
        highest_total_pos = (None, None)
        for iw in range(len(waypoints)):
            for ih, (hiw, hdist, hscore) in enumerate(hits):
                # Compute score for assigning current hit to current waypoint.
                score = hscore if iw == hiw else 0.0
                # Compute best total score, which includes this match score and
                # best of all which could come before it.
                prev_iw = iw - 1
                total_score = score
                total_score_back = (None, None)
                if prev_iw >= 0:
                    for prev_ih in range(ih + 1):
                        (prev_total_score, _) = dp[prev_iw][prev_ih]
                        new_total_score = prev_total_score + score
                        if new_total_score > total_score:
                            total_score = new_total_score
                            total_score_back = (prev_iw, prev_ih)
                dp[iw][ih] = (total_score, total_score_back)
                # Track highest score seen.
                if highest_total is None or total_score > highest_total:
                    highest_total = total_score
                    highest_total_pos = (iw, ih)
        # Traceback sequence to get scores and distance for score.
        scores = defaultdict(lambda: (0, None))
        cur_pos = highest_total_pos
        while cur_pos != (None, None):
            cur_iw, cur_ih = cur_pos
            hiw, hdist, hscore = hits[cur_ih]
            if cur_iw == hiw:
                scores[cur_iw] = (hscore, hdist)
            _, cur_pos = dp[cur_iw][cur_ih]

        # Convert to evaluation.
        waypoint_evals = []
        for iw, waypoint in enumerate(waypoints):
            score, dist = scores[iw]
            waypoint_eval = interop_admin_api_pb2.WaypointEvaluation()
            waypoint_eval.id = iw
            waypoint_eval.score_ratio = score
            if dist is not None:
                waypoint_eval.closest_for_scored_approach_ft = dist
            if iw in best:
                waypoint_eval.closest_for_mission_ft = best[iw]
            waypoint_evals.append(waypoint_eval)
        return waypoint_evals


@admin.register(UasTelemetry)
class UasTelemetryModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_display = ('pk', 'user', 'timestamp', 'latitude', 'longitude',
                    'altitude_msl', 'uas_heading')
