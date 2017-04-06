"""Targets view."""
import io
import json
from PIL import Image
import os
import os.path

from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.target import Color
from auvsi_suas.models.target import Orientation
from auvsi_suas.models.target import Shape
from auvsi_suas.models.target import Target
from auvsi_suas.models.target import TargetType
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.decorators import require_superuser
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from sendfile import sendfile


def normalize_data(data):
    """Convert received target parameters to native Python types.

    Checks whether values are valid and in-range. Skips any non-existent
    fields.

    Args:
        data: JSON-converted dictionary of target parameters

    Returns:
        data dictionary with all present target fields in native types.

    Raises:
        ValueError: Parameter not convertable or out-of-range
    """

    # 'alphanumeric' and 'description' use the empty string instead of None
    if 'alphanumeric' in data and data['alphanumeric'] is None:
        data['alphanumeric'] = ""
    if 'description' in data and data['description'] is None:
        data['description'] = ""

    # Values may be None to clear them or leave them blank.

    # Type is the one exception; it is required and may not be None.
    if 'type' in data:
        try:
            data['type'] = TargetType.lookup(data['type'])
        except KeyError:
            raise ValueError('Unknown target type "%s"; known types %r' %
                             (data['type'], TargetType.names()))

    if 'latitude' in data and data['latitude'] is not None:
        try:
            data['latitude'] = float(data['latitude'])
            if data['latitude'] < -90 or data['latitude'] > 90:
                raise ValueError
        except ValueError:
            # Unable to convert to float or out-of-range
            raise ValueError('Invalid latitude "%s", must be -90 <= lat <= 90'
                             % data['latitude'])

    if 'longitude' in data and data['longitude'] is not None:
        try:
            data['longitude'] = float(data['longitude'])
            if data['longitude'] < -180 or data['longitude'] > 180:
                raise ValueError
        except ValueError:
            # Unable to convert to float or out-of-range
            raise ValueError(
                'Invalid longitude "%s", must be -180 <= lat <= 180' %
                (data['longitude']))

    if 'orientation' in data and data['orientation'] is not None:
        try:
            data['orientation'] = Orientation.lookup(data['orientation'])
        except KeyError:
            raise ValueError('Unknown orientation "%s"; known orientations %r'
                             % (data['orientation'], Orientation.names()))

    if 'shape' in data and data['shape'] is not None:
        try:
            data['shape'] = Shape.lookup(data['shape'])
        except KeyError:
            raise ValueError('Unknown shape "%s"; known shapes %r' %
                             (data['shape'], Shape.names()))

    if 'background_color' in data and data['background_color'] is not None:
        try:
            data['background_color'] = Color.lookup(data['background_color'])
        except KeyError:
            raise ValueError('Unknown color "%s"; known colors %r' %
                             (data['background_color'], Color.names()))

    if 'alphanumeric_color' in data and data['alphanumeric_color'] is not None:
        try:
            data['alphanumeric_color'] = \
                Color.lookup(data['alphanumeric_color'])
        except KeyError:
            raise ValueError('Unknown color "%s"; known colors %r' %
                             (data['alphanumeric_color'], Color.names()))

    if 'autonomous' in data:
        if data['autonomous'] is not True and data['autonomous'] is not False:
            raise ValueError('"autonmous" must be true or false')

    if 'actionable_override' in data:
        if (data['actionable_override'] is not True and
            data['actionable_override'] is not False): # yapf: disable
            raise ValueError('"actionable_override" must be true or false')

    return data


class Targets(View):
    """POST new target."""

    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(Targets, self).dispatch(*args, **kwargs)

    def get(self, request):
        # Limit serving to 100 targets to prevent slowdown and isolation problems.
        targets = Target.objects.filter(user=request.user).all()[:100]
        targets = [t.json(is_superuser=request.user.is_superuser)
                   for t in targets]

        # Older versions of JS allow hijacking the Array constructor to steal
        # JSON data. It is not a problem in recent versions.
        return JsonResponse(targets, safe=False)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest('Request body is not valid JSON.')

        # Must be a json dictionary.
        if not isinstance(data, dict):
            return HttpResponseBadRequest('Request body not a JSON dict.')

        # Target type is required.
        if 'type' not in data:
            return HttpResponseBadRequest('Target type required.')

        # Team id can only be specified if superuser.
        user = request.user
        if 'team_id' in data:
            if request.user.is_superuser:
                user = User.objects.get(username=data['team_id'])
            else:
                return HttpResponseForbidden(
                    'Non-admin users cannot send team_id')

        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Require zero or both of latitude and longitude.
        if (latitude is not None and longitude is None) or \
            (latitude is None and longitude is not None):
            return HttpResponseBadRequest(
                'Either none or both of latitude and longitude required.')

        # Cannot submit JSON with actionable_override if not superuser.
        if 'actionable_override' in data and not request.user.is_superuser:
            return HttpResponseForbidden(
                'Non-admin users cannot submit actionable override.')

        try:
            data = normalize_data(data)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        l = None
        if latitude is not None and longitude is not None:
            l = GpsPosition(latitude=data['latitude'],
                            longitude=data['longitude'])
            l.save()

        # Use the dictionary get() method to default non-existent values to None.
        t = Target(user=user,
                   target_type=data['type'],
                   location=l,
                   orientation=data.get('orientation'),
                   shape=data.get('shape'),
                   background_color=data.get('background_color'),
                   alphanumeric=data.get('alphanumeric', ''),
                   alphanumeric_color=data.get('alphanumeric_color'),
                   description=data.get('description', ''),
                   autonomous=data.get('autonomous', False),
                   actionable_override=data.get('actionable_override', False))
        t.save()

        return JsonResponse(
            t.json(is_superuser=request.user.is_superuser),
            status=201)


def find_target(request, pk):
    """Lookup requested Target model.

    Only the request's user's targets will be returned.

    Args:
        request: Request object
        pk: Target primary key

    Raises:
        Target.DoesNotExist: pk not found
        ValueError: Target not owned by this user.
    """
    target = Target.objects.get(pk=pk)

    # We only let users get their own targets, unless a superuser.
    if target.user == request.user or request.user.is_superuser:
        return target
    else:
        raise ValueError("Accessing target %d not allowed" % pk)


class TargetsId(View):
    """Get or update a specific target."""

    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(TargetsId, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        return JsonResponse(target.json(is_superuser=
                                        request.user.is_superuser))

    def put(self, request, pk):
        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest('Request body is not valid JSON.')

        # Must be a json dictionary.
        if not isinstance(data, dict):
            return HttpResponseBadRequest('Request body not a JSON dict.')

        # Cannot submit JSON with actionable_override if not superuser.
        if 'actionable_override' in data and not request.user.is_superuser:
            return HttpResponseForbidden(
                'Non-admin users cannot submit actionable override.')

        try:
            data = normalize_data(data)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        # We update any of the included values, except id and user
        if 'type' in data:
            target.target_type = data['type']
        if 'orientation' in data:
            target.orientation = data['orientation']
        if 'shape' in data:
            target.shape = data['shape']
        if 'background_color' in data:
            target.background_color = data['background_color']
        if 'alphanumeric' in data:
            target.alphanumeric = data['alphanumeric']
        if 'alphanumeric_color' in data:
            target.alphanumeric_color = data['alphanumeric_color']
        if 'description' in data:
            target.description = data['description']
        if 'autonomous' in data:
            target.autonomous = data['autonomous']
        if 'actionable_override' in data:
            target.actionable_override = data['actionable_override']

        # Location is special because it is in a GpsPosition model

        # If lat/lon exist and are None, the user wants to clear them.
        # If they exist and are not None, the user wants to update/add them.
        # If they don't exist, the user wants to leave them alone.
        clear_lat = False
        clear_lon = False
        update_lat = False
        update_lon = False

        if 'latitude' in data:
            if data['latitude'] is None:
                clear_lat = True
            else:
                update_lat = True

        if 'longitude' in data:
            if data['longitude'] is None:
                clear_lon = True
            else:
                update_lon = True

        if (clear_lat and not clear_lon) or (not clear_lat and clear_lon):
            # Location must be cleared entirely, we can't clear just lat or
            # just lon.
            return HttpResponseBadRequest(
                'Only none or both of latitude and longitude can be cleared.')

        if clear_lat and clear_lon:
            target.location = None
        elif update_lat or update_lon:
            if target.location is not None:
                # We can directly update individual components
                if update_lat:
                    target.location.latitude = data['latitude']
                if update_lon:
                    target.location.longitude = data['longitude']
                target.location.save()
            else:
                # We need a new GpsPosition, this requires both lat and lon
                if not update_lat or not update_lon:
                    return HttpResponseBadRequest(
                        'Either none or both of latitude and longitude required.')

                l = GpsPosition(latitude=data['latitude'],
                                longitude=data['longitude'])
                l.save()
                target.location = l

        target.save()

        return JsonResponse(target.json(is_superuser=
                                        request.user.is_superuser))

    def delete(self, request, pk):
        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        # Remember the thumbnail path so we can delete it from disk.
        thumbnail = target.thumbnail.path if target.thumbnail else None

        target.delete()

        if thumbnail:
            try:
                os.remove(thumbnail)
            except OSError as e:
                logger.warning("Unable to delete thumbnail: %s", e)

        return HttpResponse("Target deleted.")


class TargetsIdImage(View):
    """Get or add/update target image."""

    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(TargetsIdImage, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        if not target.thumbnail.name:
            return HttpResponseNotFound('Target %s has no image' % pk)

        # Tell Apache to serve the thumbnail.
        return sendfile(request, target.thumbnail.path)

    def post(self, request, pk):
        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
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
                i.format)

        old_path = target.thumbnail.path if target.thumbnail else None

        target.thumbnail.save('%d.%s' % (target.pk, i.format), ImageFile(f))

        if old_path and target.thumbnail.path != old_path:
            # We didn't overwrite the old thumbnail, we should delete it,
            # but ignore deletion errors.
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
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))

        if not target.thumbnail or not target.thumbnail.path:
            return HttpResponseNotFound('Target %s has no image' % pk)

        path = target.thumbnail.path
        # Remove the thumbnail from the target.
        # Note that this does not delete it from disk!
        target.thumbnail.delete()

        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Unable to delete thumbnail: %s", e)

        return HttpResponse("Image deleted.")


class TargetsAdminReview(View):
    """Get or update review status for targets."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(TargetsAdminReview, self).dispatch(*args, **kwargs)

    def get(self, request):
        """Gets all of the targets ready for review."""
        targets = []
        for user in User.objects.all():
            # Targets still editable aren't ready for review.
            if (MissionClockEvent.user_on_clock(user) or
                    MissionClockEvent.user_on_timeout(user)):
                continue
            # Get targets which have thumbnail.
            targets.extend([t
                            for t in Target.objects.filter(user=user).all()
                            if t.thumbnail])
        # Sort targets by last edit time, convert to json.
        targets = [t.json(is_superuser=request.user.is_superuser)
                   for t in sorted(targets,
                                   key=lambda t: t.last_modified_time)]
        return JsonResponse(targets, safe=False)

    def put(self, request, pk):
        """Updates the review status of a target."""
        try:
            data = json.loads(request.body)
            thumbnail_approved = bool(data['thumbnail_approved'])
            description_approved = bool(data['description_approved'])
        except TypeError:
            return HttpResponseBadRequest('JSON not a dict.')
        except KeyError:
            return HttpResponseBadRequest('Failed to get required field.')
        except ValueError:
            return HttpResponseBadRequest('Field had incorrect type.')

        try:
            target = find_target(request, int(pk))
        except Target.DoesNotExist:
            return HttpResponseNotFound('Target %s not found' % pk)
        except ValueError as e:
            return HttpResponseForbidden(str(e))
        target.thumbnail_approved = thumbnail_approved
        target.description_approved = description_approved
        target.save()
        return JsonResponse(target.json(is_superuser=
                                        request.user.is_superuser))
