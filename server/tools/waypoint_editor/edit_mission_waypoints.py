from __future__ import print_function

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(this_dir, '..', '..')
sys.path = [server_dir] + sys.path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
from django.core.wsgi import get_wsgi_application
get_wsgi_application()

import argparse
import json
import auvsi_suas.models as models


def active_mission():
    '''Get the active mission.

    Returns:
        MissionConfig for active mission or None if there is no activate mission.

    Raises:
        ValueError: The server has multiple active missions.
'''
    missions = models.mission_config.MissionConfig.objects.filter(
        is_active=True)
    if len(missions) > 1:
        raise ValueError('Multiple active missions: %s' % missions)

    return missions[0] if missions else None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        '''Edits an interop server mission to include the waypoints specified in a JSON.

See the example_waypoints.json for reference.''',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('json_file',
                        help='The file to load the mission waypoints from',
                        nargs='?',
                        default='/dev/stdin')
    parser.add_argument(
        '--pk',
        type=int,
        default=None,
        help='Edit the specified pk rather than the currently active mission')

    args = parser.parse_args()

    # Read in JSON file
    try:
        with open(args.json_file) as f:
            wp_string = f.read()
    except IOError as e:
        print('Error: Could not read JSON file')
        print(e)
        sys.exit(1)

    # Convert json string to list of waypoints
    try:
        waypoints = json.loads(wp_string)
    except ValueError:
        print('Error: File is not a valid json')
        sys.exit(1)

    # Get the mission object to edit
    # If the pk is 0, edit the currently active mission
    if args.pk == None:
        mission = active_mission()
        if mission == None:
            print(
                'Error: Active mission not found or multiple active missions')
            sys.exit(1)
    else:
        try:
            mission = models.mission_config.MissionConfig.objects.get(
                pk=args.pk)
        except models.mission_config.MissionConfig.DoesNotExist:
            print('Error: Mission pk ' + str(args.pk) + ' does not exist')
            sys.exit(1)

    # Create new Django objects out of the waypoint list
    waypoints_objects = []
    for i, waypoint in enumerate(waypoints):
        gps_position = models.gps_position.GpsPosition.objects.create(
            latitude=waypoint['latitude'],
            longitude=waypoint['longitude'])

        aerial_position = models.aerial_position.AerialPosition.objects.create(
            gps_position=gps_position,
            altitude_msl=waypoint['altitude_msl'])

        new_wp_object = models.waypoint.Waypoint.objects.create(
            position=aerial_position,
            order=(i + 1))
        waypoints_objects.append(new_wp_object)

    # Set the mission waypoints to the new list of objects and save it
    mission.mission_waypoints = waypoints_objects
    mission.save()
    print('Successfully saved mission waypoints')
