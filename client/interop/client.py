"""Core interoperability client module

This module provides a Python interface to the SUAS interoperability API.

Users should use the AsyncClient to manage the interface, as it has performance
features. A simpler Client is also given as a base implementation.

See README.md for more details."""

from concurrent.futures import ThreadPoolExecutor
import functools
import json
import requests
import threading

from .exceptions import InteropError
from .types import Mission
from .types import MovingObstacle
from .types import StationaryObstacle
from .types import Target


class Client(object):
    """Client which provides authenticated access to interop API.

    The constructor makes a login request, and all future requests will
    automatically send the authentication cookie.

    This client uses a single session to make blocking requests to the
    interoperability server. This is the base core implementation. The
    AsyncClient uses this base Client to add performance features.
    """

    def __init__(self, url, username, password, timeout=10, max_retries=10):
        """Create a new Client and login.

        Args:
            url: Base URL of interoperability server
                (e.g., http://localhost:8000).
            username: Interoperability username.
            password: Interoperability password.
            timeout: Individual session request timeout (seconds).
            max_retries: Maximum attempts to establish a connection.
        """
        self.url = url
        self.timeout = timeout

        self.session = requests.Session()
        self.session.mount(
            'http://',
            requests.adapters.HTTPAdapter(max_retries=max_retries))

        # All endpoints require authentication, so always login.
        self.post('/api/login',
                  data={'username': username,
                        'password': password})

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

    def get_missions(self):
        """GET missions.

        Returns:
            List of Mission.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/missions')
        return [Mission.deserialize(m) for m in r.json()]

    def post_telemetry(self, telem):
        """POST new telemetry.

        Args:
            telem: Telemetry object containing telemetry state.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.post('/api/telemetry', data=telem.serialize())

    def get_obstacles(self):
        """GET obstacles.

        Returns:
            List of StationaryObstacles and list of MovingObstacles
                i.e., ([StationaryObstacle], [MovingObstacles]).
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/obstacles')
        d = r.json()

        stationary = []
        for o in d['stationary_obstacles']:
            stationary.append(StationaryObstacle.deserialize(o))

        moving = []
        for o in d['moving_obstacles']:
            moving.append(MovingObstacle.deserialize(o))

        return stationary, moving

    def get_targets(self):
        """GET targets.

        Returns:
            List of Target objects which are viewable by user.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/targets')
        return [Target.deserialize(t) for t in r.json()]

    def get_target(self, target_id):
        """GET target.

        Args:
            target_id: The ID of the target to get.
        Returns:
            Target object with corresponding ID.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.get('/api/targets/%d' % target_id)
        return Target.deserialize(r.json())

    def post_target(self, target):
        """POST target.

        Args:
            target: The target to upload.
        Returns:
            The target after upload, which will include the target ID and user.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.post('/api/targets', data=json.dumps(target.serialize()))
        return Target.deserialize(r.json())

    def put_target(self, target_id, target):
        """PUT target.

        Args:
            target_id: The ID of the target to update.
            target: The target details to update.
        Returns:
            The target after being updated.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
            ValueError or AttributeError: Malformed response from server.
        """
        r = self.put('/api/targets/%d' % target_id,
                     data=json.dumps(target.serialize()))
        return Target.deserialize(r.json())

    def delete_target(self, target_id):
        """DELETE target.

        Args:
            target_id: The ID of the target to delete.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.delete('/api/targets/%d' % target_id)

    def get_target_image(self, target_id):
        """GET target image.

        Args:
            target_id: The ID of the target for which to get the image.
        Returns:
            The image data that was previously uploaded.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        return self.get('/api/targets/%d/image' % target_id).content

    def post_target_image(self, target_id, image_data):
        """POST target image. Image must be PNG or JPEG data.

        Args:
            target_id: The ID of the target for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.put_target_image(target_id, image_data)

    def put_target_image(self, target_id, image_data):
        """PUT target image. Image must be PNG or JPEG data.

        Args:
            target_id: The ID of the target for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.put('/api/targets/%d/image' % target_id, data=image_data)

    def delete_target_image(self, target_id):
        """DELETE target image.

        Args:
            target_id: The ID of the target image to delete.
        Raises:
            InteropError: Error from server.
            requests.Timeout: Request timeout.
        """
        self.delete('/api/targets/%d/image' % target_id)


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

    def __init__(self, url, username, password, timeout=10, workers=8):
        """Create a new AsyncClient and login.

        Args:
            url: Base URL of interoperability server
                (e.g., http://localhost:8000)
            username: Interoperability username
            password: Interoperability password
            timeout: Individual session request timeout (seconds)
            workers: Number of threads to use for sending/receiving requests.
        """
        self.client = Client(url, username, password, timeout)
        self.executor = ThreadPoolExecutor(max_workers=workers)

    def get_missions(self):
        """GET missions.

        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_missions)

    def post_telemetry(self, telem):
        """POST new telemetry.

        Args:
            telem: Telemetry object containing telemetry state.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_telemetry, telem)

    def get_obstacles(self):
        """GET obstacles.

        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_obstacles)

    def get_targets(self):
        """GET targets.

        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_targets)

    def get_target(self, target_id):
        """GET target.

        Args:
            target_id: The ID of the target to get.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_target, target_id)

    def post_target(self, target):
        """POST target.

        Args:
            target: The target to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_target, target)

    def put_target(self, target_id, target):
        """PUT target.

        Args:
            target_id: The ID of the target to update.
            target: The target details to update.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.put_target, target_id, target)

    def delete_target(self, target_id):
        """DELETE target.

        Args:
            target_id: The ID of the target to delete.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.delete_target, target_id)

    def get_target_image(self, target_id):
        """GET target image.

        Args:
            target_id: The ID of the target for which to get the image.
        Returns:
            The image data that was previously uploaded.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.get_target_image, target_id)

    def post_target_image(self, target_id, image_data):
        """POST target image. Image must be PNG or JPEG data.

        Args:
            target_id: The ID of the target for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.post_target_image, target_id,
                                    image_data)

    def put_target_image(self, target_id, image_data):
        """PUT target image. Image must be PNG or JPEG data.

        Args:
            target_id: The ID of the target for which to upload an image.
            image_data: The image data (bytes loaded from file) to upload.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.put_target_image, target_id,
                                    image_data)

    def delete_target_image(self, target_id):
        """DELETE target image.

        Args:
            target_id: The ID of the target image to delete.
        Returns:
            Future object which contains the return value or error from the
            underlying Client.
        """
        return self.executor.submit(self.client.delete_target_image, target_id)
