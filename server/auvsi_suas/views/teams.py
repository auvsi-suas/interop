"""Teams view."""

import json
import logging
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.proto import interop_api_pb2
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.json import ProtoJsonEncoder
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View
from google.protobuf import json_format

logger = logging.getLogger(__name__)


def team_proto(user):
    """Generate TeamStatus proto for team."""
    team_status_proto = interop_api_pb2.TeamStatus()
    team_status_proto.team.id = user.pk
    team_status_proto.team.username = user.username
    team_status_proto.team.name = user.first_name
    team_status_proto.team.university = user.last_name
    team_status_proto.in_air = TakeoffOrLandingEvent.user_in_air(user)

    telemetry = UasTelemetry.last_for_user(user)
    if telemetry is not None:
        telemetry_proto = team_status_proto.telemetry
        telemetry_proto.latitude = telemetry.latitude
        telemetry_proto.longitude = telemetry.longitude
        telemetry_proto.altitude = telemetry.altitude_msl
        telemetry_proto.heading = telemetry.uas_heading
        team_status_proto.telemetry_id = telemetry.pk
        team_status_proto.telemetry_age_sec = (
            timezone.now() - telemetry.timestamp).total_seconds()
        team_status_proto.telemetry_timestamp = telemetry.timestamp.isoformat()

    return team_status_proto


class Teams(View):
    """Gets a list of all teams."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(Teams, self).dispatch(*args, **kwargs)

    def get(self, request):
        users = User.objects.all()
        teams = []

        for user in users:
            # Only standard users are exported
            if not user.is_superuser:
                teams.append(team_proto(user))

        return HttpResponse(json.dumps(teams, cls=ProtoJsonEncoder),
                            content_type="application/json")


class Team(View):
    """GET a specific team."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(Team, self).dispatch(*args, **kwargs)

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponseBadRequest('Unknown team %s' % username)

        return HttpResponse(json_format.MessageToJson(team_proto(user)),
                            content_type="application/json")
