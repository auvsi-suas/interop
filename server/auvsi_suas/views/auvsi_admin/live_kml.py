from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.patches.simplekml_patch import Kml
from auvsi_suas.patches.simplekml_patch import RefreshMode
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.missions import active_mission
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic import View


class LiveKml(View):
    """ Generates a KML for live display.
    This KML uses a network link to update via the update.kml endpoint
    """

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(LiveKml, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='AUVSI SUAS LIVE Flight Data')
        kml_mission = kml.newfolder(name='Missions')

        (mission, err) = active_mission()
        if err:
            return err
        MissionConfig.kml_all(kml_mission, [mission])

        kml_flyzone = kml.newfolder(name='Fly Zones')
        FlyZone.kml_all(kml_flyzone)

        parameters = '?sessionid={}'.format(request.COOKIES['sessionid'])
        uri = request.build_absolute_uri(
            '/auvsi_admin/update.kml') + parameters

        netlink = kml.newnetworklink(name="Live Data")
        netlink.link.href = uri
        netlink.link.refreshmode = RefreshMode.oninterval
        netlink.link.refreshinterval = 0.5

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=live.kml'
        response['Content-Length'] = str(len(response.content))
        return response


def set_request_session_from_cookie(func):
    def wrapper(request):
        # Check if a sessionid has been provided
        if 'sessionid' not in request.GET:
            return HttpResponseForbidden()

        try:
            # pack the params back into the cookie
            request.COOKIES['sessionid'] = request.GET['sessionid']

            # Update the user associated with the cookie
            session = Session.objects.get(session_key=request.GET['sessionid'])
            uid = session.get_decoded().get('_auth_user_id')
            request.user = User.objects.get(pk=uid)
        except ObjectDoesNotExist:
            return HttpResponseForbidden()
        else:
            return func(request)

    return wrapper


class LiveKmlUpdate(View):
    """Generates the live update portion of LiveKml"""

    @method_decorator(set_request_session_from_cookie)
    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(LiveKmlUpdate, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='LIVE Data')
        MovingObstacle.live_kml(kml, timedelta(seconds=5))
        UasTelemetry.live_kml(kml, timedelta(seconds=5))

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=update.kml'
        response['Content-Length'] = str(len(response.content))
        return response
