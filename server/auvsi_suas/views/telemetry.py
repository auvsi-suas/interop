"""Telemetry view."""

import logging
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.proto import interop_api_pb2
from auvsi_suas.views.decorators import require_login
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from google.protobuf import json_format

logger = logging.getLogger(__name__)


class Telemetry(View):
    """GET/POST telemetry."""
    @method_decorator(require_login)
    def post(self, request):
        """Posts the UAS position with a POST request."""
        telemetry_proto = interop_api_pb2.Telemetry()
        try:
            json_format.Parse(request.body, telemetry_proto)
        except Exception as e:
            return HttpResponseBadRequest(
                'Failed to parse request. Error: %s' % str(e))

        if (not telemetry_proto.HasField('latitude')
                or not telemetry_proto.HasField('longitude')
                or not telemetry_proto.HasField('altitude')
                or not telemetry_proto.HasField('heading')):
            return HttpResponseBadRequest('Request missing fields.')

        # Check the values make sense.
        if telemetry_proto.latitude < -90 or telemetry_proto.latitude > 90:
            return HttpResponseBadRequest(
                'Latitude out of range [-90, 90]: %f' %
                telemetry_proto.latitude)
        if telemetry_proto.longitude < -180 or telemetry_proto.longitude > 180:
            return HttpResponseBadRequest(
                'Longitude out of range [-180, 180]: %f' %
                telemetry_proto.longitude)
        if telemetry_proto.altitude < -1500 or telemetry_proto.altitude > 330000:
            return HttpResponseBadRequest(
                'Altitude out of range [-1500, 330000]: %f' %
                telemetry_proto.altitude)
        if telemetry_proto.heading < 0 or telemetry_proto.heading > 360:
            return HttpResponseBadRequest('Heading out of range [0, 360]: %f' %
                                          telemetry_proto.heading)

        # Store telemetry.
        telemetry = UasTelemetry(user=request.user,
                                 latitude=telemetry_proto.latitude,
                                 longitude=telemetry_proto.longitude,
                                 altitude_msl=telemetry_proto.altitude,
                                 uas_heading=telemetry_proto.heading)
        telemetry.save()

        return HttpResponse('UAS Telemetry Successfully Posted.')
