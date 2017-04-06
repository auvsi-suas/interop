"""Tests for the mission_evaluation module."""

from django.contrib.auth.models import User
from django.test import TestCase

from auvsi_suas.models import mission_evaluation
from auvsi_suas.models import mission_config
from auvsi_suas.proto import mission_pb2


class TestMissionScoring(TestCase):
    """Tests the score conversion for the mission_evaluation module."""

    def setUp(self):
        """Create a base evaluation to save redefining it."""
        self.eval = mission_pb2.MissionEvaluation()
        self.eval.team = 'team'
        feedback = self.eval.feedback
        feedback.mission_clock_time_sec = 60 * 10
        feedback.uas_telemetry_time_max_sec = 1.0
        feedback.uas_telemetry_time_avg_sec = 1.0
        feedback.out_of_bounds_time_sec = 10
        feedback.boundary_violations = 2
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0.5
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0.2
        obs = feedback.stationary_obstacles.add()
        obs.hit = True
        obs = feedback.stationary_obstacles.add()
        obs.hit = False
        obs = feedback.moving_obstacles.add()
        obs.hit = True
        obs = feedback.moving_obstacles.add()
        obs.hit = True
        targets = feedback.target
        targets.score_ratio = 0.56
        t = targets.targets.add()
        t.score_ratio = 0.96
        t.classifications_score_ratio = 0.6
        t.geolocation_score_ratio = 0.2
        t.actionable_score_ratio = 1.0
        t.autonomous_score_ratio = 1.0
        t.interop_score_ratio = 1.0
        t = targets.targets.add()
        t.score_ratio = 0.16
        t.classifications_score_ratio = 0.2
        t.geolocation_score_ratio = 0.6
        t.actionable_score_ratio = 0.0
        t.autonomous_score_ratio = 0.0
        t.interop_score_ratio = 0.0
        judge = feedback.judge
        judge.flight_time_sec = 60 * 6
        judge.post_process_time_sec = 60 * 4
        judge.used_timeout = True
        judge.safety_pilot_takeovers = 2
        judge.manual_flight_time_sec = 60 * 1
        judge.waypoints_captured = 2
        judge.out_of_bounds = 2
        judge.unsafe_out_of_bounds = 1
        judge.air_delivery_accuracy_ft = 50
        judge.operational_excellence_percent = 90

    def test_timeline(self):
        """Test the timeline scoring."""
        judge = self.eval.feedback.judge
        timeline = self.eval.score.timeline

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.84888889, timeline.mission_time)
        self.assertAlmostEqual(0, timeline.mission_penalty)
        self.assertAlmostEqual(0, timeline.timeout)
        self.assertAlmostEqual(0.67911111, timeline.score_ratio)

        judge.flight_time_sec = 60 * 50
        judge.used_timeout = False
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.0, timeline.mission_time)
        self.assertAlmostEqual(4.32, timeline.mission_penalty)
        self.assertAlmostEqual(1, timeline.timeout)
        self.assertAlmostEqual(-4.12, timeline.score_ratio)


class TestMissionEvaluation(TestCase):
    """Tests the mission_evaluation module."""
    fixtures = ['testdata/sample_mission.json']

    def test_evaluate_teams(self):
        """Tests the evaluation of teams method."""
        user0 = User.objects.get(username='user0')
        user1 = User.objects.get(username='user1')
        config = mission_config.MissionConfig.objects.get()

        mission_eval = mission_evaluation.evaluate_teams(config)

        # Contains user0 and user1
        self.assertEqual(2, len(mission_eval.teams))

        # user0 data
        user_eval = mission_eval.teams[0]
        self.assertEqual(user0.username, user_eval.team)
        feedback = user_eval.feedback
        score = user_eval.score
        self.assertEqual(0.0,
                         feedback.waypoints[0].closest_for_scored_approach_ft)
        self.assertEqual(1.0, feedback.waypoints[0].score_ratio)
        self.assertEqual(0.0,
                         feedback.waypoints[1].closest_for_scored_approach_ft)
        self.assertAlmostEqual(2, feedback.mission_clock_time_sec)
        self.assertAlmostEqual(0.6, feedback.out_of_bounds_time_sec)

        self.assertAlmostEqual(0.5, feedback.uas_telemetry_time_max_sec)
        self.assertAlmostEqual(1. / 6, feedback.uas_telemetry_time_avg_sec)

        self.assertAlmostEqual(0.445, feedback.target.score_ratio, places=3)

        self.assertEqual(25, feedback.stationary_obstacles[0].id)
        self.assertEqual(True, feedback.stationary_obstacles[0].hit)
        self.assertEqual(26, feedback.stationary_obstacles[1].id)
        self.assertEqual(False, feedback.stationary_obstacles[1].hit)

        self.assertEqual(25, feedback.moving_obstacles[0].id)
        self.assertEqual(True, feedback.moving_obstacles[0].hit)
        self.assertEqual(26, feedback.moving_obstacles[1].id)
        self.assertEqual(False, feedback.moving_obstacles[1].hit)

        self.assertEqual(1, feedback.judge.flight_time_sec)

        self.assertAlmostEqual(0.99948148, score.timeline.mission_time)
        self.assertAlmostEqual(0, score.timeline.mission_penalty)
        self.assertAlmostEqual(1, score.timeline.timeout)
        self.assertAlmostEqual(0.99958519, score.timeline.score_ratio)

        # user1 data
        user_eval = mission_eval.teams[1]
        self.assertEqual(user1.username, user_eval.team)
        feedback = user_eval.feedback
        score = user_eval.score
        self.assertEqual(0.0,
                         feedback.waypoints[0].closest_for_scored_approach_ft)
        self.assertEqual(1.0, feedback.waypoints[0].score_ratio)
        self.assertEqual(0.0,
                         feedback.waypoints[1].closest_for_scored_approach_ft)
        self.assertAlmostEqual(18, feedback.mission_clock_time_sec)
        self.assertAlmostEqual(1.0, feedback.out_of_bounds_time_sec)

        self.assertAlmostEqual(2.0, feedback.uas_telemetry_time_max_sec)
        self.assertAlmostEqual(1.0, feedback.uas_telemetry_time_avg_sec)

        self.assertAlmostEqual(0, feedback.target.score_ratio, places=3)

        self.assertEqual(25, feedback.stationary_obstacles[0].id)
        self.assertEqual(False, feedback.stationary_obstacles[0].hit)
        self.assertEqual(26, feedback.stationary_obstacles[1].id)
        self.assertEqual(False, feedback.stationary_obstacles[1].hit)

        self.assertEqual(25, feedback.moving_obstacles[0].id)
        self.assertEqual(False, feedback.moving_obstacles[0].hit)
        self.assertEqual(26, feedback.moving_obstacles[1].id)
        self.assertEqual(False, feedback.moving_obstacles[1].hit)

        self.assertEqual(2, feedback.judge.flight_time_sec)

        self.assertAlmostEqual(0.99918519, score.timeline.mission_time)
        self.assertAlmostEqual(0, score.timeline.mission_penalty)
        self.assertAlmostEqual(0, score.timeline.timeout)
        self.assertAlmostEqual(0.79934815, score.timeline.score_ratio)

    def test_evaluate_teams_specific_users(self):
        """Tests the evaluation of teams method with specific users."""
        user0 = User.objects.get(username='user0')
        user1 = User.objects.get(username='user1')
        config = mission_config.MissionConfig.objects.get()

        mission_eval = mission_evaluation.evaluate_teams(config, [user0])

        self.assertEqual(1, len(mission_eval.teams))
        self.assertEqual(user0.username, mission_eval.teams[0].team)
