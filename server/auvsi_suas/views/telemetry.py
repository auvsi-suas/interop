"""Telemetry view."""

import iso8601
import json
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.decorators import require_superuser
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View


class Telemetry(View):
    """GET/POST telemetry."""

    @method_decorator(require_login)
    def post(self, request):
        """Posts the UAS position with a POST request.

        User must send a POST request with the following paramters:
        latitude: A latitude in decimal degrees.
        longitude: A logitude in decimal degrees.
        altitude_msl: An MSL altitude in decimal feet.
        uas_heading: The UAS (true north) heading in decimal degrees.
        """
        try:
            # Get the parameters
            latitude = float(request.POST['latitude'])
            longitude = float(request.POST['longitude'])
            altitude_msl = float(request.POST['altitude_msl'])
            uas_heading = float(request.POST['uas_heading'])
        except KeyError:
            # Failed to get POST parameters
            logger.warning(
                'User did not specify all params for uas telemetry request.')
            logger.debug(request)
            return HttpResponseBadRequest(
                'Posting UAS position must contain POST parameters "latitude", '
                '"longitude", "altitude_msl", and "uas_heading".')
        except ValueError:
            # Failed to convert parameters
            logger.warning(
                'User specified a param which could not converted to an ' +
                'appropriate type.')
            logger.debug(request)
            return HttpResponseBadRequest(
                'Failed to convert provided POST parameters to correct form.')
        else:
            # Check the values make sense
            if latitude < -90 or latitude > 90:
                logger.warning('User specified latitude out of valid range.')
                logger.debug(request)
                return HttpResponseBadRequest(
                    'Must provide latitude between -90 and 90 degrees.')
            if longitude < -180 or longitude > 180:
                logger.warning('User specified longitude out of valid range.')
                logger.debug(request)
                return HttpResponseBadRequest(
                    'Must provide longitude between -180 and 180 degrees.')
            if uas_heading < 0 or uas_heading > 360:
                logger.warning('User specified altitude out of valid range.')
                logger.debug(request)
                return HttpResponseBadRequest(
                    'Must provide heading between 0 and 360 degrees.')

            # Store telemetry
            logger.info('User uploaded telemetry: %s' % request.user.username)

            gpos = GpsPosition(latitude=latitude, longitude=longitude)
            gpos.save()

            apos = AerialPosition(gps_position=gpos, altitude_msl=altitude_msl)
            apos.save()

            telemetry = UasTelemetry(user=request.user,
                                     uas_position=apos,
                                     uas_heading=uas_heading)
            telemetry.save()

            return HttpResponse('UAS Telemetry Successfully Posted.')

    @method_decorator(require_superuser)
    def get(self, request):
        limit = 100
        user = None
        since = None
        before = None

        if 'limit' in request.GET:
            try:
                limit = int(request.GET['limit'])
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid limit '%s'" % \
                                                request.GET['limit'])

        if 'user' in request.GET:
            try:
                user_id = int(request.GET['user'])
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid user '%s'" % \
                                                request.GET['user'])
            try:
                user = User.objects.filter(pk=user_id).get()
            except User.DoesNotExist:
                return HttpResponseBadRequest("Unknown user '%s'" % \
                                                request.GET['user'])

        # since is non-inclusive
        if 'since' in request.GET:
            try:
                since = iso8601.parse_date(request.GET['since'])
            except iso8601.ParseError:
                return HttpResponseBadRequest("Bad timestamp '%s'" % \
                                                request.GET['since'])

        # before is non-inclusive
        if 'before' in request.GET:
            try:
                before = iso8601.parse_date(request.GET['before'])
            except iso8601.ParseError:
                return HttpResponseBadRequest("Bad timestamp '%s'" % \
                                                request.GET['before'])

        # Prefetch data from all ForeignKeys (e.g., AerialPosition) when
        # evaluating the query.  This allows us to avoid making hundreds
        # of other queries as we access all of those fields.
        query = UasTelemetry.objects.select_related()

        if user:
            query = query.filter(user=user)

        if since:
            query = query.filter(timestamp__gt=since)

        if before:
            query = query.filter(timestamp__lt=before)

        logs = query.order_by('-timestamp').all()[:limit]

        response = [l.json() for l in logs]

        return HttpResponse(
            json.dumps(response),
            content_type="application/json")
