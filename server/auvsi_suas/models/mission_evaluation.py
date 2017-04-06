"""Mission evaluation."""

import datetime
import itertools
import logging
from django.conf import settings
from django.contrib.auth.models import User

from auvsi_suas.models import distance
from auvsi_suas.models import units
from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.mission_judge_feedback import MissionJudgeFeedback
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.target import Target
from auvsi_suas.models.target import TargetEvaluator
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.proto import mission_pb2

# Logging for the module
logger = logging.getLogger(__name__)


def generate_feedback(mission_config, user, team_eval):
    """Generates mission feedback for the given team and mission.

    Args:
        mission_config: The mission to evaluate the team against.
        user: The team user object for which to evaluate and provide feedback.
        team_eval: The team evaluation to fill.
    """
    feedback = team_eval.feedback

    # Calculate the total mission clock time.
    missions = MissionClockEvent.missions(user)
    mission_clock_time = datetime.timedelta(seconds=0)
    for mission in missions:
        duration = mission.duration()
        if duration is None:
            team_eval.warnings.append('Infinite mission clock.')
        else:
            mission_clock_time += duration
    feedback.mission_clock_time_sec = mission_clock_time.total_seconds()

    # Find the user's flights.
    flight_periods = TakeoffOrLandingEvent.flights(user)
    for period in flight_periods:
        if period.duration() is None:
            team_eval.warnings.append('Infinite flight period.')
    uas_period_logs = [
        UasTelemetry.dedupe(logs)
        for logs in UasTelemetry.by_time_period(user, flight_periods)
    ]
    uas_logs = list(itertools.chain.from_iterable(uas_period_logs))
    if not uas_logs:
        team_eval.warnings.append('No UAS telemetry logs.')

    # Determine interop telemetry rates.
    telem_max, telem_avg = UasTelemetry.rates(user,
                                              flight_periods,
                                              time_period_logs=uas_period_logs)
    if telem_max:
        feedback.uas_telemetry_time_max_sec = telem_max
    if telem_avg:
        feedback.uas_telemetry_time_avg_sec = telem_avg

    # Determine if the uas went out of bounds. This must be done for
    # each period individually so time between periods isn't counted as
    # out of bounds time. Note that this calculates reported time out
    # of bounds, not actual or possible time spent out of bounds.
    out_of_bounds = datetime.timedelta(seconds=0)
    feedback.boundary_violations = 0
    for logs in uas_period_logs:
        bv, bt = FlyZone.out_of_bounds(mission_config.fly_zones.all(), logs)
        feedback.boundary_violations += bv
        out_of_bounds += bt
    feedback.out_of_bounds_time_sec = out_of_bounds.total_seconds()

    # Determine if the uas hit the waypoints.
    feedback.waypoints.extend(UasTelemetry.satisfied_waypoints(
        mission_config.home_pos, mission_config.mission_waypoints.order_by(
            'order'), uas_logs))

    # Evaluate the targets.
    user_targets = Target.objects.filter(user=user).all()
    evaluator = TargetEvaluator(user_targets, mission_config.targets.all())
    feedback.target.CopyFrom(evaluator.evaluate())

    # Determine collisions with stationary and moving obstacles.
    for obst in mission_config.stationary_obstacles.all():
        obst_eval = feedback.stationary_obstacles.add()
        obst_eval.id = obst.pk
        obst_eval.hit = obst.evaluate_collision_with_uas(uas_logs)
    for obst in mission_config.moving_obstacles.all():
        obst_eval = feedback.moving_obstacles.add()
        obst_eval.id = obst.pk
        obst_eval.hit = obst.evaluate_collision_with_uas(uas_logs)

    # Add judge feedback.
    try:
        judge_feedback = MissionJudgeFeedback.objects.get(
            mission=mission_config.pk,
            user=user.pk)
        feedback.judge.CopyFrom(judge_feedback.proto())
    except MissionJudgeFeedback.DoesNotExist:
        team_eval.warnings.append('No MissionJudgeFeedback for team.')

    # Sanity check mission time.
    judge_mission_clock = (
        feedback.judge.flight_time_sec + feedback.judge.post_process_time_sec)
    if abs(feedback.mission_clock_time_sec - judge_mission_clock) > 30:
        team_eval.warnings.append(
            'Mission clock differs between interop and judge.')


def score_team(team_eval):
    """Generates a score from the given feedback.

    Args:
        team_eval: A auvsi_suas.proto.MissionEvaluation for the team.
    """
    feedback = team_eval.feedback
    score = team_eval.score

    # Score timeline.
    flight_points = feedback.judge.flight_time_sec * settings.FLIGHT_TIME_SEC_TO_POINTS
    process_points = feedback.judge.post_process_time_sec * settings.PROCESS_TIME_SEC_TO_POINTS
    total_time_points = max(
        0, settings.MISSION_TIME_TOTAL_POINTS - flight_points - process_points)
    score.timeline.mission_time = total_time_points / settings.MISSION_TIME_TOTAL_POINTS
    total_time = feedback.judge.flight_time_sec + feedback.judge.post_process_time_sec
    over_time = max(0, total_time - settings.MISSION_MAX_TIME_SEC)
    score.timeline.mission_penalty = over_time * settings.MISSION_TIME_PENALTY_FROM_SEC
    score.timeline.timeout = 0 if feedback.judge.used_timeout else 1
    score.timeline.score_ratio = (
        (settings.MISSION_TIME_WEIGHT * score.timeline.mission_time) +
        (settings.TIMEOUT_WEIGHT *
         score.timeline.timeout) - score.timeline.mission_penalty)

    # TODO(pmtischler): Rest of scoring.


def evaluate_teams(mission_config, users=None):
    """Evaluates the teams (non admin users) of the competition.

    Args:
        mission_config: The mission to evaluate users against.
        users: Optional list of users to eval. If None will evaluate all.
    Returns:
        A auvsi_suas.proto.MultiUserMissionEvaluation.
    """
    # Start a results map from user to MissionEvaluation.
    mission_eval = mission_pb2.MultiUserMissionEvaluation()

    # If not provided, eval all users.
    if users is None:
        users = User.objects.all()

    logger.info('Starting team evaluations.')
    for user in users:
        # Ignore admins.
        if user.is_superuser:
            continue

        # Start the evaluation data structure.
        logger.info('Evaluation starting for user: %s.' % user.username)
        team_eval = mission_eval.teams.add()
        team_eval.team = user.username
        # Generate feedback.
        generate_feedback(mission_config, user, team_eval)
        # Generate score from feedback.
        score_team(team_eval)

    return mission_eval
