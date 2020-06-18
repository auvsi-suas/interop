"""Map model."""

import logging
from auvsi_suas.models import pb_utils
from auvsi_suas.proto import interop_admin_api_pb2
from django.conf import settings
from django.contrib import admin
from django.db import models

logger = logging.getLogger(__name__)


class Map(models.Model):
    """Map submission for a team."""

    # The mission this is a map for.
    mission = models.ForeignKey('MissionConfig', on_delete=models.CASCADE)
    # The user which submitted and owns this map.
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             db_index=True,
                             on_delete=models.CASCADE)

    # Uploaded map.
    uploaded_map = models.ImageField(upload_to='maps', blank=True)

    # Quality assigned by a judge.
    quality = models.IntegerField(choices=pb_utils.FieldChoicesFromEnum(
        interop_admin_api_pb2.MapEvaluation.MapQuality),
                                  null=True,
                                  blank=True)


@admin.register(Map)
class MapModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('mission', )
    list_display = ('pk', 'mission', 'user', 'quality')
