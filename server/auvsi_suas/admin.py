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


# Define model admin which has scrollable select boxes
# By default on chrome select has overflow-x: hidden
class ScollableFilterModelAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("auvsi_suas/admin/scroll_filter.css", )}

# Register models for admin page

# Only display raw ID fields for ForeignKeys which may contain large amounts
# of data.

# Use filter_horizontal for ManyToMany fields to easier choose items


@admin.register(AerialPosition)
class AerialPositionModelAdmin(LargeDataModelAdmin):
    raw_id_fields = ("gps_position", )
    show_full_result_count = False


@admin.register(MissionConfig)
class MissionConfigModelAdmin(ScollableFilterModelAdmin):
    raw_id_fields = ("home_pos", "emergent_last_known_pos",
                     "off_axis_target_pos", "air_drop_pos")
    filter_vertical = ("fly_zones", "mission_waypoints", "search_grid_points",
                       "targets", "stationary_obstacles", "moving_obstacles")


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


@admin.register(FlyZone)
class FlyZoneModelAdmin(ScollableFilterModelAdmin):
    filter_vertical = ("boundary_pts", )


@admin.register(MovingObstacle)
class MovingObstacleModelAdmin(ScollableFilterModelAdmin):
    filter_vertical = ("waypoints", )

# These don't require any raw fields.
admin.site.register(GpsPosition, LargeDataModelAdmin)
admin.site.register(MissionClockEvent)
admin.site.register(MissionJudgeFeedback)
admin.site.register(TakeoffOrLandingEvent)
