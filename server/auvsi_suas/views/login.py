"""Interoperability login view."""

import logging
from auvsi_suas.proto.interop_api_pb2 import Credentials
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.views.generic import View
from google.protobuf import json_format

logger = logging.getLogger(__name__)


class Login(View):
    """Logs the user in with a POST request using the given parameters."""
    def post(self, request):
        creds = Credentials()
        try:
            json_format.Parse(request.body, creds)
        except Exception as e:
            return HttpResponseBadRequest(
                'Failed to parse request. Error: %s' % str(e))

        if not creds.HasField('username') or not creds.HasField('password'):
            return HttpResponseBadRequest('Request missing fields.')

        user = authenticate(username=creds.username, password=creds.password)
        if user is not None and user.is_active:
            # Successful authentication with active user, login
            login(request, user)
            return HttpResponse('User logged in: %s' % user.username)
        else:
            # Invalid user credentials, invalid request
            return HttpResponse(
                'Invalid credentials in request. Could not log in.',
                status=401)
