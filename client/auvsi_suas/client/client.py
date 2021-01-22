"""Core interoperability client module

This module provides a Python interface to the SUAS interoperability API.

Users should use the AsyncClient to manage the interface, as it has performance
features. A simpler Client is also given as a base implementation.
"""

import json
import requests
from auvsi_suas.client.exceptions import InteropError
from auvsi_suas.proto import interop_api_pb2
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import json_format


class Client(object):
    """Client which provides authenticated access to interop API.

    The constructor makes a login request, and all future requests will
    automatically send the authentication cookie.

    This client uses a single session to make blocking requests to the
    interoperability server. This is the base core implementation. The
    AsyncClient uses this base Client to add performance features.
    """
    def __init__(self,
                 url,
                 username,
                 password,
                 timeout=10,
                 max_concurrent=128,
                 max_retries=10):
        """Create a new Client and login.

        Args:
            url: Base URL of interoperability server
                (e.g., http://localhost:8000).
            username: Interoperability username.
            password: Interoperability password.
            timeout: Individual session request timeout (seconds).
            max_concurrent: Maximum number of concurrent requests.
            max_retries: Maximum attempts to establish a connection.
        """
        self.url = url
        self.username = username
        self.timeout = timeout
        self.max_concurrent = 128

        self.session = requests.Session()
        self.session.mount(
            'http://',
            requests.adapters.HTTPAdapter(pool_maxsize=max_concurrent,
                                          max_retries=max_retries))

        # All endpoints require authentication, so always login.
        creds = interop_api_pb2.Credentials()
        creds.username = username
        creds.password = password
        self.post('/api/login', data=json_format.MessageToJson(creds))

    def get(self, uri, **kwargs):
        """GET request to server.

        Args:
            uri: Server URI to access (without base URL).
            **kwargs: Arguments to requests.Session.get method.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        r = self.session.get(self.url + uri, timeout=self.timeout, **kwargs)
        if not r.ok:
            raise InteropError(r)
        return r

    def post(self, uri, **kwargs):
        """POST request to server.

        Args:
            uri: Server URI to access (without base URL).
            **kwargs: Arguments to requests.Session.post method.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        r = self.session.post(self.url + uri, timeout=self.timeout, **kwargs)
        if not r.ok:
            raise InteropError(r)
        return r

    def put(self, uri, **kwargs):
        """PUT request to server.

        Args:
            uri: Server URI to access (without base URL).
            **kwargs: Arguments to requests.Session.put method.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        r = self.session.put(self.url + uri, timeout=self.timeout, **kwargs)
        if not r.ok:
            raise InteropError(r)
        return r

    def delete(self, uri):
        """DELETE request to server.

        Args:
            uri: Server URI to access (without base URL).
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        r = self.session.delete(self.url + uri, timeout=self.timeout)
        if not r.ok:
            raise InteropError(r)
        return r

    def get_teams(self):
        """GET the status of teams.

        Returns:
            List of TeamStatus objects for active teams.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/teams')
        teams = []
        for team_dict in r.json():
            team_proto = interop_api_pb2.TeamStatus()
            json_format.Parse(json.dumps(team_dict), team_proto)
            teams.append(team_proto)
        return teams

    def get_mission(self, mission_id):
        """GET a mission by ID.

        Returns:
            Mission.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/missions/%d' % mission_id)
        mission = interop_api_pb2.Mission()
        json_format.Parse(r.text, mission)
        return mission

    def post_telemetry(self, telem):
        """POST new telemetry.

        Args:
            telem: Telemetry object containing telemetry state.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.post('/api/telemetry', data=json_format.MessageToJson(telem))

    def get_odlcs(self, mission=None):
        """GET odlcs.

        Args:
            mission: Optional. ID of a mission to restrict by.
        Returns:
            List of Odlc objects which are viewable by user.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        url = '/api/odlcs'
        if mission:
            url += '?mission=%d' % mission
        r = self.get(url)
        odlcs = []
        for odlc_dict in r.json():
            odlc_proto = interop_api_pb2.Odlc()
            json_format.Parse(json.dumps(odlc_dict), odlc_proto)
            odlcs.append(odlc_proto)
        return odlcs

    def get_odlc(self, odlc_id):
        """GET odlc.

        Args:
            odlc_id: The ID of the odlc to get.
        Returns:
            Odlc object with corresponding ID.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/odlcs/%d' % odlc_id)
        odlc = interop_api_pb2.Odlc()
        json_format.Parse(r.text, odlc)
        return odlc

    def post_odlc(self, odlc):
        """POST odlc.

        Args:
            odlc: The odlc to upload.
        Returns:
            The odlc after upload, which will include the odlc ID and user.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.post('/api/odlcs', data=json_format.MessageToJson(odlc))
        odlc = interop_api_pb2.Odlc()
        json_format.Parse(r.text, odlc)
        return odlc

    def put_odlc(self, odlc_id, odlc):
        """PUT odlc.

        Args:
            odlc_id: The ID of the odlc to update.
            odlc: The odlc details to update.
        Returns:
            The odlc after being updated.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.put('/api/odlcs/%d' % odlc_id,
                     data=json_format.MessageToJson(odlc))
        odlc = interop_api_pb2.Odlc()
        json_format.Parse(r.text, odlc)
        return odlc

    def delete_odlc(self, odlc_id):
        """DELETE odlc.

        Args:
            odlc_id: The ID of the odlc to delete.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.delete('/api/odlcs/%d' % odlc_id)

    def get_odlc_image(self, odlc_id):
        """GET odlc image.

        Args:
            odlc_id: The ID of the odlc for which to get the image.
        Returns:
            The image data that was previously uploaded.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        return self.get('/api/odlcs/%d/image' % odlc_id).content

    def post_odlc_image(self, odlc_id, image_data):
        """POST odlc image. Image must be PNG or JPEG data.

        Args:
            odlc_id: The ID of the odlc for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.put_odlc_image(odlc_id, image_data)

    def put_odlc_image(self, odlc_id, image_data):
        """PUT odlc image. Image must be PNG or JPEG data.

        Args:
            odlc_id: The ID of the odlc for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.put('/api/odlcs/%d/image' % odlc_id, data=image_data)

    def delete_odlc_image(self, odlc_id):
        """DELETE odlc image.

        Args:
            odlc_id: The ID of the odlc image to delete.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.delete('/api/odlcs/%d/image' % odlc_id)

    def get_map_image(self, mission_id):
        """GET map image.

        Args:
            mission_id: The mission for which to get the uploaded map.
        Returns:
            The image data that was previously uploaded.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        return self.get('/api/maps/%d/%s' %
                        (mission_id, self.username)).content

    def put_map_image(self, mission_id, image_data):
        """PUT map image. Image must be PNG or JPEG data.

        Args:
            mission_id: The mission for which to upload a map.
            image_data: The image data (bytes loaded from file) to upload.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.put('/api/maps/%d/%s' % (mission_id, self.username),
                 data=image_data)

    def delete_map_image(self, mission_id):
        """DELETE map image.

        Args:
            mission_id: The mission for which to delete an uploaded a map.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.delete('/api/maps/%d/%s' % (mission_id, self.username))


class AsyncClient(object):
    """Client which uses the base to be more performant.

    This client uses Futures with a ThreadPoolExecutor. This allows requests to
    be executed asynchronously. Asynchronous execution with multiple Clients
    enables requests to be processed in parallel and with pipeline execution at
    the server, which can drastically improve achievable interoperability rate
    as observed at the client.

    Note that methods return Future objects. Users should handle the response
    and errors appropriately. If serial request execution is desired, ensure the
    Future response or error is received prior to making another request.
    """
    def __init__(self,
                 url,
                 username,
                 password,
                 timeout=10,
                 max_concurrent=128,
                 max_retries=10):
        """Create a new AsyncClient and login.

        Args:
            url: Base URL of interoperability server
                (e.g., http://localhost:8000)
            username: Interoperability username
            password: Interoperability password
            timeout: Individual session request timeout (seconds)
            max_concurrent: Maximum number of concurrent requests.
            max_retries: Maximum attempts to establish a connection.
        """
        self.client = Client(url, username, password, timeout, max_concurrent,
                             max_retries)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def get_teams(self):
        """GET the status of teams.

        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_teams)

    def get_mission(self, mission_id):
        """GET a mission by ID.

        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_mission, mission_id)

    def post_telemetry(self, telem):
        """POST new telemetry.

        Args:
            telem: Telemetry object containing telemetry state.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_telemetry, telem)

    def get_odlcs(self, mission=None):
        """GET odlcs.

        Args:
            mission: Optional. ID of a mission to restrict by.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_odlcs, mission)

    def get_odlc(self, odlc_id):
        """GET odlc.

        Args:
            odlc_id: The ID of the odlc to get.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_odlc, odlc_id)

    def post_odlc(self, odlc):
        """POST odlc.

        Args:
            odlc: The odlc to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_odlc, odlc)

    def put_odlc(self, odlc_id, odlc):
        """PUT odlc.

        Args:
            odlc_id: The ID of the odlc to update.
            odlc: The odlc details to update.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.put_odlc, odlc_id, odlc)

    def delete_odlc(self, odlc_id):
        """DELETE odlc.

        Args:
            odlc_id: The ID of the odlc to delete.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.delete_odlc, odlc_id)

    def get_odlc_image(self, odlc_id):
        """GET odlc image.

        Args:
            odlc_id: The ID of the odlc for which to get the image.
        Returns:
            The image data that was previously uploaded.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_odlc_image, odlc_id)

    def post_odlc_image(self, odlc_id, image_data):
        """POST odlc image. Image must be PNG or JPEG data.

        Args:
            odlc_id: The ID of the odlc for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_odlc_image, odlc_id,
                                    image_data)

    def put_odlc_image(self, odlc_id, image_data):
        """PUT odlc image. Image must be PNG or JPEG data.

        Args:
            odlc_id: The ID of the odlc for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.put_odlc_image, odlc_id,
                                    image_data)

    def delete_odlc_image(self, odlc_id):
        """DELETE odlc image.

        Args:
            odlc_id: The ID of the odlc image to delete.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.delete_odlc_image, odlc_id)

    def get_map_image(self, mission_id):
        """GET map image.

        Args:
            mission_id: The mission for which to get the uploaded map.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_map_image, mission_id)

    def put_map_image(self, mission_id, image_data):
        """PUT map image. Image must be PNG or JPEG data.

        Args:
            mission_id: The mission for which to upload a map.
            image_data: The image data (bytes loaded from file) to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.put_map_image, mission_id,
                                    image_data)

    def delete_map_image(self, mission_id):
        """DELETE map image.

        Args:
            mission_id: The mission for which to delete an uploaded a map.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.delete_map_image, mission_id)
