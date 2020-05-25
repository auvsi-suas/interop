"""Odlcs view."""
from PIL import Image
import io
import json
import logging
import os
import os.path
import re
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.odlc import Odlc
from auvsi_suas.proto import interop_admin_api_pb2
from auvsi_suas.proto import interop_api_pb2
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.json import ProtoJsonEncoder
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views.generic import View
from google.protobuf import json_format
from sendfile import sendfile

logger = logging.getLogger(__name__)

ALPHANUMERIC_RE = re.compile(r"^[A-Z0-9]$")

ODLC_MAX = 20  # Limit in the rules.
ODLC_BUFFER = 2  # Buffer for swaps.
ODLC_UPLOAD_LIMIT = (ODLC_MAX + ODLC_BUFFER) * 2  # Account for auto/not.


def odlc_to_proto(odlc):
    """Converts an ODLC into protobuf format."""
    odlc_proto = interop_api_pb2.Odlc()
    odlc_proto.id = odlc.pk
    odlc_proto.mission = odlc.mission.pk
    odlc_proto.type = odlc.odlc_type
    if odlc.location is not None:
        odlc_proto.latitude = odlc.location.latitude
        odlc_proto.longitude = odlc.location.longitude
    if odlc.orientation is not None:
        odlc_proto.orientation = odlc.orientation
    if odlc.shape is not None:
        odlc_proto.shape = odlc.shape
    if odlc.alphanumeric:
        odlc_proto.alphanumeric = odlc.alphanumeric
    if odlc.shape_color is not None:
        odlc_proto.shape_color = odlc.shape_color
    if odlc.alphanumeric_color is not None:
        odlc_proto.alphanumeric_color = odlc.alphanumeric_color
    if odlc.description:
        odlc_proto.description = odlc.description
    odlc_proto.autonomous = odlc.autonomous
    return odlc_proto


def validate_odlc_proto(odlc_proto):
    """Validates ODLC proto, raising ValueError if invalid."""
    if not odlc_proto.HasField('mission'):
        raise ValueError('ODLC mission is required.')

    try:
        MissionConfig.objects.get(pk=odlc_proto.mission)
    except MissionConfig.DoesNotExist:
        raise ValueError('Mission for ODLC does not exist.')

    if not odlc_proto.HasField('type'):
        raise ValueError('ODLC type is required.')

    if odlc_proto.HasField('latitude') != odlc_proto.HasField('longitude'):
        raise ValueError('Must specify both latitude and longitude.')

    if odlc_proto.HasField('latitude') and (odlc_proto.latitude < -90
                                            or odlc_proto.latitude > 90):
        raise ValueError('Invalid latitude "%f", must be -90 <= lat <= 90' %
                         odlc_proto.latitude)

    if odlc_proto.HasField('longitude') and (odlc_proto.longitude < -180
                                             or odlc_proto.longitude > 180):
        raise ValueError('Invalid longitude "%s", must be -180 <= lat <= 180' %
                         odlc_proto.longitude)

    if (odlc_proto.HasField('alphanumeric')
            and ALPHANUMERIC_RE.fullmatch(odlc_proto.alphanumeric) is None):
        raise ValueError('Alphanumeric is invalid.')


def update_odlc_from_proto(odlc, odlc_proto):
    """Sets fields of the ODLC from the proto format."""
    odlc.mission_id = odlc_proto.mission
    odlc.odlc_type = odlc_proto.type

    if odlc_proto.HasField('latitude') and odlc_proto.HasField('longitude'):
        if odlc.location is None:
            l = GpsPosition(latitude=odlc_proto.latitude,
                            longitude=odlc_proto.longitude)
            l.save()
            odlc.location = l
        else:
            odlc.location.latitude = odlc_proto.latitude
            odlc.location.longitude = odlc_proto.longitude
            odlc.location.save()
    else:
        # Don't delete underlying GPS position in case it's shared by admin.
        # Just unreference it.
        odlc.location = None

    if odlc_proto.HasField('orientation'):
        odlc.orientation = odlc_proto.orientation
    else:
        odlc.orientation = None

    if odlc_proto.HasField('shape'):
        odlc.shape = odlc_proto.shape
    else:
        odlc.shape = None

    if odlc_proto.HasField('alphanumeric'):
        odlc.alphanumeric = odlc_proto.alphanumeric
    else:
        odlc.alphanumeric = ''

    if odlc_proto.HasField('shape_color'):
        odlc.shape_color = odlc_proto.shape_color
    else:
        odlc.shape_color = None

    if odlc_proto.HasField('alphanumeric_color'):
        odlc.alphanumeric_color = odlc_proto.alphanumeric_color
    else:
        odlc.alphanumeric_color = None

    if odlc_proto.HasField('description'):
        odlc.description = odlc_proto.description
    else:
        odlc.description = ''

    if odlc_proto.HasField('autonomous'):
        odlc.autonomous = odlc_proto.autonomous
    else:
        odlc.autonomous = False


class Odlcs(View):
    """POST new odlc."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(Odlcs, self).dispatch(*args, **kwargs)

    def get(self, request):
        # Restrict ODLCs to those for user, and optionally a mission.
        odlcs = Odlc.objects.filter(user=request.user)
        if 'mission' in request.GET:
            try:
                mission_id = int(request.GET['mission'])
            except:
                return HttpResponseBadRequest('Provided invalid mission ID.')
            odlcs = odlcs.filter(mission=mission_id)

        # Limit serving to 100 odlcs to prevent slowdown and isolation problems.
        odlcs = odlcs.all()[:100]

        odlc_protos = [odlc_to_proto(o) for o in odlcs]
        return HttpResponse(json.dumps(odlc_protos, cls=ProtoJsonEncoder),
                            content_type="application/json")

    def post(self, request):
        odlc_proto = interop_api_pb2.Odlc()
        try:
            json_format.Parse(request.body, odlc_proto)
        except Exception as e:
            return HttpResponseBadRequest(
                'Failed to parse request. Error: %s' % str(e))
        # Validate ODLC proto fields.
        try:
            validate_odlc_proto(odlc_proto)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        # Cannot set ODLC ID on a post.
        if odlc_proto.HasField('id'):
            return HttpResponseBadRequest(
                'Cannot specify ID for POST request.')

        # Check that there aren't too many ODLCs uploaded already.
        odlc_count = Odlc.objects.filter(user=request.user).filter(
            mission=odlc_proto.mission).count()
        if odlc_count >= ODLC_UPLOAD_LIMIT:
            return HttpResponseBadRequest(
                'Reached upload limit for ODLCs for mission.')

        # Build the ODLC object from the request.
        odlc = Odlc()
        odlc.user = request.user
        update_odlc_from_proto(odlc, odlc_proto)
        odlc.save()

        return HttpResponse(json_format.MessageToJson(odlc_to_proto(odlc)),
                            content_type="application/json")


def find_odlc(request, pk):
    """Lookup requested Odlc model.

    Only the request's user's odlcs will be returned.

    Args:
        request: Request object
        pk: Odlc primary key

    Raises:
        Odlc.DoesNotExist: pk not found
        ValueError: Odlc not owned by this user.
    """
    odlc = Odlc.objects.get(pk=pk)

    # We only let users get their own odlcs, unless a superuser.
    if odlc.user == request.user or request.user.is_superuser:
        return odlc
    else:
        raise ValueError("Accessing odlc %d not allowed" % pk)


class OdlcsId(View):
    """Get or update a specific odlc."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(OdlcsId, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        return HttpResponse(json_format.MessageToJson(odlc_to_proto(odlc)),
                            content_type="application/json")

    def put(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        odlc_proto = interop_api_pb2.Odlc()
        try:
            json_format.Parse(request.body, odlc_proto)
        except Exception as e:
            return HttpResponseBadRequest(
                'Failed to parse request. Error: %s' % str(e))
        # Validate ODLC proto fields.
        try:
            validate_odlc_proto(odlc_proto)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        # ID provided in proto must match object.
        if odlc_proto.HasField('id') and odlc_proto.id != odlc.pk:
            return HttpResponseBadRequest('ID in request does not match URL.')

        # Update the ODLC object from the request.
        update_odlc_from_proto(odlc, odlc_proto)
        odlc.update_last_modified()
        odlc.save()

        return HttpResponse(json_format.MessageToJson(odlc_to_proto(odlc)),
                            content_type="application/json")

    def delete(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        # Remember the thumbnail path so we can delete it from disk.
        thumbnail = odlc.thumbnail.path if odlc.thumbnail else None

        odlc.delete()

        if thumbnail:
            try:
                os.remove(thumbnail)
            except OSError as e:
                logger.warning("Unable to delete thumbnail: %s", e)

        return HttpResponse("Odlc deleted.")


class OdlcsIdImage(View):
    """Get or add/update odlc image."""
    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(OdlcsIdImage, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        if not odlc.thumbnail or not odlc.thumbnail.name:
            return HttpResponseNotFound('Odlc %s has no image' % pk)

        # Tell sendfile to serve the thumbnail.
        return sendfile(request, odlc.thumbnail.path)

    def post(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

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

        # Clear thumbnail review state.
        if odlc.thumbnail_approved is not None:
            odlc.thumbnail_approved = None

        # Save the thumbnail, note old path.
        old_path = odlc.thumbnail.path if odlc.thumbnail else None
        odlc.thumbnail.save('%d.%s' % (odlc.pk, i.format), ImageFile(f))

        # ODLC has been modified.
        odlc.update_last_modified()
        odlc.save()

        # Check whether old thumbnail should be deleted. Ignore errors.
        if old_path and odlc.thumbnail.path != old_path:
            try:
                os.remove(old_path)
            except OSError as e:
                logger.warning("Unable to delete old thumbnail: %s", e)

        return HttpResponse("Image uploaded.")

    def put(self, request, pk):
        """We simply make PUT do the same as POST."""
        return self.post(request, pk)

    def delete(self, request, pk):
        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        if not odlc.thumbnail or not odlc.thumbnail.path:
            return HttpResponseNotFound('Odlc %s has no image' % pk)

        # Clear thumbnail review state.
        if odlc.thumbnail_approved is not None:
            odlc.thumbnail_approved = None
            odlc.save()

        path = odlc.thumbnail.path
        # Remove the thumbnail from the odlc.
        # Note that this does not delete it from disk!
        odlc.thumbnail.delete()

        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Unable to delete thumbnail: %s", e)

        return HttpResponse("Image deleted.")


def odlc_to_review_proto(odlc):
    """Converts an ODLC into a review proto."""
    review_proto = interop_admin_api_pb2.OdlcReview()
    review_proto.odlc.CopyFrom(odlc_to_proto(odlc))
    review_proto.last_modified_timestamp = odlc.last_modified_time.isoformat()
    if odlc.thumbnail_approved is not None:
        review_proto.thumbnail_approved = odlc.thumbnail_approved
    if odlc.description_approved is not None:
        review_proto.description_approved = odlc.description_approved
    return review_proto


def update_odlc_from_review_proto(odlc, review_proto):
    """Sets fields of the ODLC from the review."""
    if review_proto.HasField('thumbnail_approved'):
        odlc.thumbnail_approved = review_proto.thumbnail_approved
    else:
        odlc.thumbnail_approved = False
    if review_proto.HasField('description_approved'):
        odlc.description_approved = review_proto.description_approved
    else:
        odlc.description_approved = False


class OdlcsAdminReview(View):
    """Get or update review status for odlcs."""
    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(OdlcsAdminReview, self).dispatch(*args, **kwargs)

    def get(self, request):
        """Gets all of the odlcs ready for review."""
        # Get all odlcs which have a thumbnail to review.
        odlcs = [t for t in Odlc.objects.all() if t.thumbnail]

        # Sort odlcs by last edit time.
        odlcs.sort(key=lambda t: t.last_modified_time)

        # Convert to review protos.
        odlc_review_protos = [odlc_to_review_proto(odlc) for odlc in odlcs]

        return HttpResponse(json.dumps(odlc_review_protos,
                                       cls=ProtoJsonEncoder),
                            content_type="application/json")

    def put(self, request, pk):
        """Updates the review status of a odlc."""
        review_proto = interop_admin_api_pb2.OdlcReview()
        try:
            json_format.Parse(request.body, review_proto)
        except Exception:
            return HttpResponseBadRequest('Failed to parse review proto.')

        try:
            odlc = find_odlc(request, int(pk))
        except Odlc.DoesNotExist:
            return HttpResponseNotFound('Odlc %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        update_odlc_from_review_proto(odlc, review_proto)
        odlc.save()

        return HttpResponse(json_format.MessageToJson(
            odlc_to_review_proto(odlc)),
                            content_type="application/json")
