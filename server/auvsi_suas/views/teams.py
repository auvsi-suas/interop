"""Teams view."""
import json
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_superuser
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View


def user_json(user):
    """Generate JSON-style dict for user."""
    telemetry = UasTelemetry.last_for_user(user)
    return {
        'name': user.username,
        'id': user.pk,
        'on_clock': MissionClockEvent.user_on_clock(user),
        'on_timeout': MissionClockEvent.user_on_timeout(user),
        'in_air': TakeoffOrLandingEvent.user_in_air(user),
        'telemetry': telemetry.json() if telemetry else None
    }


class Teams(View):
    """Gets a list of all teams."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(Teams, self).dispatch(*args, **kwargs)

    def get(self, request):
        users = User.objects.all()
        teams = []

        for user in users:
            # Only standard users are exported
            if not user.is_superuser:
                teams.append(user_json(user))

        return HttpResponse(json.dumps(teams), content_type="application/json")


class TeamsId(View):
    """GET/PUT specific team."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(TeamsId, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=int(pk))
        except User.DoesNotExist:
            return HttpResponseBadRequest('Unknown team %s' % pk)

        return HttpResponse(
            json.dumps(user_json(user)),
            content_type="application/json")

    def put(self, request, pk):
        """PUT allows updating status."""
        try:
            user = User.objects.get(pk=int(pk))
        except User.DoesNotExist:
            return HttpResponseBadRequest('Unknown team %s' % pk)
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest('Invalid JSON: %s' % request.body)

        # Potential events to update.
        takeoff_event = None
        clock_event = None
        # Update whether UAS is in air.
        if 'in_air' in data:
            in_air = data['in_air']
            if not isinstance(in_air, bool):
                return HttpResponseBadRequest('in_air must be boolean')

            currently_in_air = TakeoffOrLandingEvent.user_in_air(user)
            # New event only necessary if changing status
            if currently_in_air != in_air:
                takeoff_event = TakeoffOrLandingEvent(user=user,
                                                      uas_in_air=in_air)
        # Update whether UAS in on clock or timeout.
        if 'on_clock' in data or 'on_timeout' in data:
            currently_on_clock = MissionClockEvent.user_on_clock(user)

            currently_on_timeout = MissionClockEvent.user_on_timeout(user)
            on_clock = data.get('on_clock', currently_on_clock)
            on_timeout = data.get('on_timeout', currently_on_timeout)
            if (not isinstance(on_clock, bool) or
                    not isinstance(on_timeout, bool)):
                return HttpResponseBadRequest(
                    'on_clock and on_timeout must be boolean.')
            if on_clock and on_timeout:
                return HttpResponseBadRequest(
                    'Cannot be on mission clock and on timeout.')
            # New event only necessary if changing status
            if (on_clock != currently_on_clock or
                    on_timeout != currently_on_timeout):
                clock_event = MissionClockEvent(user=user,
                                                team_on_clock=on_clock,
                                                team_on_timeout=on_timeout)
        # Request was valid. Save updates.
        if takeoff_event:
            takeoff_event.save()
        if clock_event:
            clock_event.save()

        return HttpResponse(
            json.dumps(user_json(user)),
            content_type="application/json")
