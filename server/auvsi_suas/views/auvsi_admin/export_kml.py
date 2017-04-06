from auvsi_suas.models.fly_zone import FlyZone
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.patches.simplekml_patch import Kml
from auvsi_suas.views.decorators import require_superuser
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View


class ExportKml(View):
    """ Generates a KML file HttpResponse"""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(ExportKml, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='AUVSI SUAS Flight Data')
        kml_teams = kml.newfolder(name='Teams')
        kml_mission = kml.newfolder(name='Missions')
        users = User.objects.all()
        for user in users:
            # Ignore admins
            if user.is_superuser:
                continue
            UasTelemetry.kml(user=user,
                             logs=UasTelemetry.by_user(user),
                             kml=kml_teams,
                             kml_doc=kml.document)
        MissionConfig.kml_all(kml_mission)
        kml_flyzone = kml.newfolder(name='Fly Zones')
        FlyZone.kml_all(kml_flyzone)

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=mission.kml'
        response['Content-Length'] = str(len(response.content))
        return response
