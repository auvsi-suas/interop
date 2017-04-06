from django.contrib import admin
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.mission_judge_feedback import MissionJudgeFeedback
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.target import Target
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.models.waypoint import Waypoint


# Define model admin which has better defaults for large amounts of data.
class LargeDataModelAdmin(admin.ModelAdmin):
    show_full_result_count = False

# Register models for admin page

# Only display raw ID fields for ForeignKeys which may contain large amounts
# of data.


@admin.register(AerialPosition)
class AerialPositionModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("gps_position", )
    show_full_result_count = False


@admin.register(MissionConfig)
class MissionConfigModelAdmin(admin.ModelAdmin):
    raw_id_fields = ("home_pos", "emergent_last_known_pos",
                     "off_axis_target_pos", "air_drop_pos")


@admin.register(StationaryObstacle)
class StationaryObstacleModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("gps_position", )


@admin.register(Target)
class TargetModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("location", )


@admin.register(UasTelemetry)
class UasTelemetryModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("uas_position", )
    show_full_result_count = False


@admin.register(Waypoint)
class WaypointModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("position", )

# These don't require any raw fields.
admin.site.register(FlyZone)
admin.site.register(GpsPosition, LargeDataModelAdmin)
admin.site.register(MissionClockEvent)
admin.site.register(MissionJudgeFeedback)
admin.site.register(MovingObstacle)
admin.site.register(TakeoffOrLandingEvent)
