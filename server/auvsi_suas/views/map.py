"""Map view."""

from PIL import Image
import io
import json
import logging
import os
import os.path
from auvsi_suas.models.map import Map
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.proto import interop_admin_api_pb2
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.decorators import require_superuser
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.generic import View
from sendfile import sendfile

logger = logging.getLogger(__name__)


def find_map(mission_pk, user_pk):
    """Lookup requested Map model.

    Only the request's user's map will be returned.

    Args:
        mission_pk: Mission primary key.
        user_pk: The user which owns the map.

    Raises:
        Map.DoesNotExist: Map not found
    """
    return Map.objects.get(mission_id=mission_pk, user_id=user_pk)


class MapImage(View):
    """Get or update a map."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(MapImage, self).dispatch(*args, **kwargs)

    def get(self, request, mission_pk, username):
        mission_pk = int(mission_pk)

        if username != request.user.username and not request.user.is_superuser:
            return HttpResponseForbidden(
                'User [%s] is not able to access maps owned by user [%s]' %
                (request.user.username, username))

        try:
            m = find_map(mission_pk, request.user.pk)
        except Map.DoesNotExist:
            return HttpResponseNotFound('Map not found.')

        if not m.uploaded_map or not m.uploaded_map.name:
            return HttpResponseNotFound('Map not found.')

        # Tell sendfile to serve the map.
        return sendfile(request, m.uploaded_map.path)

    def put(self, request, mission_pk, username):
        mission_pk = int(mission_pk)

        if username != request.user.username and not request.user.is_superuser:
            return HttpResponseForbidden(
                'User [%s] is not able to access maps owned by user [%s]' %
                (request.user.username, username))

        try:
            m = find_map(mission_pk, request.user.pk)
        except:
            m = Map()
            m.mission_id = mission_pk
            m.user = request.user

        # Request body is the file
        f = io.BytesIO(request.body)

        # Verify that this is a valid image
        try:
            i = Image.open(f)
            i.verify()
        except IOError as e:
            return HttpResponseBadRequest(str(e))

        if i.format not in ['JPEG', 'PNG']:
            return HttpResponseBadRequest(
                'Invalid image format %s, only JPEG and PNG allowed' %
                (i.format))

        # Clear review state.
        if m.quality is not None:
            m.quality = None

        # Save the map, note old path.
        old_path = m.uploaded_map.path if m.uploaded_map else None
        m.uploaded_map.save(
            '%d-%d.%s' % (mission_pk, request.user.pk, i.format), ImageFile(f))

        # Map has been updated.
        m.save()

        # Check whether old map should be deleted. Ignore errors.
        if old_path and m.uploaded_map.path != old_path:
            try:
                os.remove(old_path)
            except OSError as e:
                logger.warning("Unable to delete old map: %s", e)

        return HttpResponse("Map uploaded.")

    def delete(self, request, mission_pk, username):
        mission_pk = int(mission_pk)

        if username != request.user.username and not request.user.is_superuser:
            return HttpResponseForbidden(
                'User [%s] is not able to access maps owned by user [%s]' %
                (request.user.username, username))

        try:
            m = find_map(mission_pk, request.user.pk)
        except:
            return HttpResponseNotFound('Map not found.')

        if not m.uploaded_map or not m.uploaded_map.path:
            return HttpResponseNotFound('Map not found.')

        path = m.uploaded_map.path

        # Delete the map. Note this does not cleanup the image.
        m.delete()

        # Delete the image file.
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Unable to delete map: %s", e)

        return HttpResponse("Map deleted.")
