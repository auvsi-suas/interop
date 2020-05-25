"""Feedback from judges on mission performance."""

import logging
from auvsi_suas.models import pb_utils
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.proto import interop_admin_api_pb2
from django.conf import settings
from django.contrib import admin
from django.core import validators
from django.db import models

logger = logging.getLogger(__name__)


class MissionJudgeFeedback(models.Model):
    """Stores feedback from judges on a team's mission performance."""

    # The mission for which this is feedback.
    mission = models.ForeignKey(MissionConfig, on_delete=models.CASCADE)
    # The user for which this is feedback.
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # Time spent occupying runway and airspace.
    flight_time = models.DurationField()
    # Time spent handling data on mission clock.
    post_process_time = models.DurationField()
    # Whether the team used their single timeout.
    used_timeout = models.BooleanField()

    # Whether the team had the min auto flight time.
    min_auto_flight_time = models.BooleanField()
    # The number of times the pilot took over.
    safety_pilot_takeovers = models.IntegerField(validators=[
        validators.MinValueValidator(0),
    ])
    # Number of times the UAS went out of bounds.
    out_of_bounds = models.IntegerField(validators=[
        validators.MinValueValidator(0),
    ])
    # Number of times out of bounds compromised safety.
    unsafe_out_of_bounds = models.IntegerField(validators=[
        validators.MinValueValidator(0),
    ])
    # Whether something fell off UAS during flight.
    things_fell_off_uas = models.BooleanField()
    # Whether the UAS crashed.
    crashed = models.BooleanField()

    # Accuracy of drop in feet.
    air_drop_accuracy = models.IntegerField(
        choices=pb_utils.FieldChoicesFromEnum(
            interop_admin_api_pb2.MissionJudgeFeedback.AirDropAccuracy))
    # Whether the UGV drove to the specified location.
    ugv_drove_to_location = models.BooleanField()

    # Grade of team performance [0, 100].
    operational_excellence_percent = models.FloatField(validators=[
        validators.MinValueValidator(0),
        validators.MaxValueValidator(100),
    ])

    class Meta:
        unique_together = (('mission', 'user'), )

    def proto(self):
        """Get the proto formatted feedback."""
        feedback = interop_admin_api_pb2.MissionJudgeFeedback()

        feedback.flight_time_sec = self.flight_time.total_seconds()
        feedback.post_process_time_sec = self.post_process_time.total_seconds()
        feedback.used_timeout = self.used_timeout

        feedback.min_auto_flight_time = self.min_auto_flight_time
        feedback.safety_pilot_takeovers = self.safety_pilot_takeovers
        feedback.out_of_bounds = self.out_of_bounds
        feedback.unsafe_out_of_bounds = self.unsafe_out_of_bounds
        feedback.things_fell_off_uas = self.things_fell_off_uas
        feedback.crashed = self.crashed

        feedback.air_drop_accuracy = self.air_drop_accuracy
        feedback.ugv_drove_to_location = self.ugv_drove_to_location

        feedback.operational_excellence_percent = self.operational_excellence_percent

        return feedback


@admin.register(MissionJudgeFeedback)
class MissionJudgeFeedbackModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_display = ('pk', 'mission', 'user', 'flight_time',
                    'post_process_time', 'used_timeout',
                    'min_auto_flight_time', 'safety_pilot_takeovers',
                    'out_of_bounds', 'unsafe_out_of_bounds',
                    'things_fell_off_uas', 'crashed', 'air_drop_accuracy',
                    'ugv_drove_to_location', 'operational_excellence_percent')
