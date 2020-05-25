from auvsi_suas.views.login import Login
from auvsi_suas.views.index import Index
from auvsi_suas.views.missions import Evaluate
from auvsi_suas.views.missions import ExportKml
from auvsi_suas.views.missions import LiveKml
from auvsi_suas.views.missions import LiveKmlUpdate
from auvsi_suas.views.missions import MissionDetails
from auvsi_suas.views.missions import Missions
from auvsi_suas.views.missions import MissionsId
from auvsi_suas.views.odlcs import Odlcs
from auvsi_suas.views.odlcs import OdlcsAdminReview
from auvsi_suas.views.odlcs import OdlcsId
from auvsi_suas.views.odlcs import OdlcsIdImage
from auvsi_suas.views.teams import Teams
from auvsi_suas.views.teams import Team
from auvsi_suas.views.telemetry import Telemetry
from auvsi_suas.views.utils import BulkCreateTeams
from auvsi_suas.views.utils import GpsConversion
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'auvsi_suas'

# yapf: disable
urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('api/login', Login.as_view(), name='login'),
    path('api/missions', Missions.as_view(), name='missions'),
    path('api/missions/<int:pk>', MissionsId.as_view(), name='missions_id'),
    path('api/missions/<int:pk>/evaluate.zip', Evaluate.as_view(), name='evaluate'),
    path('api/missions/<int:pk>/mission.html', MissionDetails.as_view(), name='details'),
    path('api/missions/export.kml', ExportKml.as_view(), name='export_kml'),
    path('api/missions/live.kml', LiveKml.as_view(), name='live_kml'),
    path('api/missions/update.kml', LiveKmlUpdate.as_view(), name='update_kml'),
    path('api/odlcs', Odlcs.as_view(), name='odlcs'),
    path('api/odlcs/<int:pk>', OdlcsId.as_view(), name='odlcs_id'),
    path('api/odlcs/<int:pk>/image', OdlcsIdImage.as_view(), name='odlcs_id_image'),
    path('api/odlcs/review', OdlcsAdminReview.as_view(), name='odlcs_review'),
    path('api/odlcs/review/<int:pk>', OdlcsAdminReview.as_view(), name='odlcs_review_id'),
    path('api/teams', Teams.as_view(), name='teams'),
    path('api/teams/<str:username>', Team.as_view(), name='team'),
    path('api/telemetry', Telemetry.as_view(), name='telemetry'),
    path('api/utils/gps_conversion', GpsConversion.as_view(), name='gps_conversion'),
    path('api/utils/bulk_create_teams', BulkCreateTeams.as_view(), name='bulk_create_teams'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# yapf: enable
