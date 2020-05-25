"""Utilities for admins."""

import csv
import ipaddress
import json
import logging
import random
from LatLon23 import string2latlon
from auvsi_suas.proto import interop_admin_api_pb2
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.json import ProtoJsonEncoder
from django import shortcuts
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from google.protobuf import json_format

logger = logging.getLogger(__name__)

LATLON_FORMAT = 'H%d%-%m%-%S'

INTEROP_SERVER_IP = '10.10.130.10'
INTEROP_SERVER_PORT = 80
INTEROP_TEAM_STATIC_RANGE_MIN = '10.10.130.20'
INTEROP_TEAM_STATIC_RANGE_MAX = '10.10.130.119'


class GpsConversion(View):
    """Converts GPS from string to decimal."""
    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(GpsConversion, self).dispatch(*args, **kwargs)

    def post(self, request):
        request_proto = interop_admin_api_pb2.GpsConversionRequest()
        try:
            json_format.Parse(request.body, request_proto)
        except Exception as e:
            return HttpResponseBadRequest(
                'Failed to parse request. Error: %s' % str(e))

        if not request_proto.HasField(
                'latitude') or not request_proto.HasField('longitude'):
            return HttpResponseBadRequest('Request missing fields.')

        try:
            latlon = string2latlon(request_proto.latitude,
                                   request_proto.longitude, LATLON_FORMAT)
        except Exception as e:
            return HttpResponseBadRequest('Failed to convert GPS. Error: %s' %
                                          str(e))

        response = interop_admin_api_pb2.GpsConversionResponse()
        response.latitude = latlon.lat.decimal_degree
        response.longitude = latlon.lon.decimal_degree

        return HttpResponse(json_format.MessageToJson(response),
                            content_type="application/json")


class BulkCreateTeams(View):
    """Creates teams based on CSV file and renders a printable webpage."""
    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(BulkCreateTeams, self).dispatch(*args, **kwargs)

    def post(self, request):
        # Generate the base context for credentials.
        context = {
            'server': {
                'ip': INTEROP_SERVER_IP,
                'port': INTEROP_SERVER_PORT,
            },
            'teams': [],
        }

        # Compute the numeric form of IP address.
        # Compute the range for wrap-around.
        static_min = int(
            ipaddress.IPv4Address(str(INTEROP_TEAM_STATIC_RANGE_MIN)))
        static_max = int(
            ipaddress.IPv4Address(str(INTEROP_TEAM_STATIC_RANGE_MAX)))
        static_range = static_max - static_min

        # Load the CSV input, generate team credentials.
        random.seed()
        csvreader = csv.DictReader(
            request.FILES['file'].read().decode().splitlines())
        for i, row in enumerate(csvreader):
            context['teams'].append({
                'university':
                row['University'],
                'name':
                row['Name'],
                'username':
                row['Username'],
                'password':
                random.randint(1e9, 1e10),
                'ip':
                str(ipaddress.IPv4Address(static_min + (i % static_range))),
            })

        # Insert the user accounts.
        # Trim fields due to database constraints.
        for team in context['teams']:
            get_user_model().objects.create_user(
                username=team['username'],
                password=team['password'],
                first_name=team['name'][:30],
                last_name=team['university'][:30])

        # Render a printable page.
        return shortcuts.render(request, 'bulk_create_teams.html', context)
