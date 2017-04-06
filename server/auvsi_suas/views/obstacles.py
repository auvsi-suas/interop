"""Interoperability obstacles view."""

import iso8601
import json
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.stationary_obstacle import StationaryObstacle
from auvsi_suas.views import boolean_param
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.missions import active_mission
from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View


class Obstacles(View):
    """Gets the obstacle information as JSON with a GET request."""

    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(Obstacles, self).dispatch(*args, **kwargs)

    def get(self, request):
        time = timezone.now()

        # ?time=TIMESTAMP to get obstacle location at specific time
        if 'time' in request.GET:
            if not request.user.is_superuser:
                return HttpResponseBadRequest(
                    'Only superusers may set the time parameter')

            try:
                time = iso8601.parse_date(request.GET['time'])
            except iso8601.ParseError:
                return HttpResponseBadRequest("Bad timestamp '%s'" % \
                                                request.GET['time'])

        # Log user access to obstacle info
        logger.info('User downloaded obstacle info: %s.' %
                    request.user.username)

        # Get active mission for forming responses.
        (mission, err) = active_mission()
        if err:
            return err

        # Form JSON response portion for stationary obstacles
        stationary_obstacles_cached = True
        stationary_obstacles_key = '/StationaryObstacle/all'
        stationary_obstacles = cache.get(stationary_obstacles_key)
        if stationary_obstacles is None:
            stationary_obstacles = mission.stationary_obstacles.all()
            stationary_obstacles_cached = False
        stationary_obstacles_json = []
        for cur_obst in stationary_obstacles:
            # Add current obstacle
            cur_obst_json = cur_obst.json()
            stationary_obstacles_json.append(cur_obst_json)

        # Form JSON response portion for moving obstacles
        moving_obstacles_cached = True
        moving_obstacles_key = '/MovingObstacle/all'
        moving_obstacles = cache.get(moving_obstacles_key)
        if moving_obstacles is None:
            moving_obstacles = mission.moving_obstacles.all()
            moving_obstacles_cached = False
        moving_obstacles_json = []
        for cur_obst in moving_obstacles:
            # Add current obstacle
            cur_obst_json = cur_obst.json(time=time)
            moving_obstacles_json.append(cur_obst_json)

        # Form final JSON response
        data = {
            'stationary_obstacles': stationary_obstacles_json,
            'moving_obstacles': moving_obstacles_json
        }

        # Cache obstacles for next request
        if not stationary_obstacles_cached:
            cache.set(stationary_obstacles_key, stationary_obstacles)
        if not moving_obstacles_cached:
            cache.set(moving_obstacles_key, moving_obstacles)

        # Return JSON data
        return HttpResponse(json.dumps(data), content_type="application/json")
