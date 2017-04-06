"""Tests for the moving_obstacle module."""

import datetime
import time
from auvsi_suas.models import units
from auvsi_suas.models.aerial_position import AerialPosition
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.moving_obstacle import MovingObstacle
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.models.waypoint import Waypoint
from auvsi_suas.patches.simplekml_patch import Kml
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

TESTDATA_COMPETITION_DIST = [
    (-76.428709, 38.145306, -76.426375, 38.146146, 0.22446),
    (-76.428537, 38.145399, -76.427818, 38.144686, 0.10045),
    (-76.434261, 38.142471, -76.418876, 38.147838, 1.46914)
]

# (lat, lon, rad, alt)
TESTDATA_MOVOBST_CONTAINSPOS_OBJ = (-76, 38, 100, 200)
# (lat, lon, alt)
TESTDATA_MOVOBST_CONTAINSPOS_INSIDE = [
    (-76, 38, 100),
    (-76, 38, 300),
    (-76.0002, 38, 200),
    (-76, 38.0003, 200)
]  # yapf: disable
TESTDATA_MOVOBST_CONTAINSPOS_OUTSIDE = [
    (-76, 38, 99),
    (-76, 38, 301),
    (-76.0003, 38, 200),
    (-76, 38.004, 200)
]  # yapf: disable

TESTDATA_MOVOBST_PATHS = [
    # Test 2 points
    [(38.142233, -76.434082, 300),
     (38.141878, -76.425198, 700)],
    # Test 3 points
    [(38.142233, -76.434082, 300),
     (38.141878, -76.425198, 700),
     (38.144599, -76.428186, 100)],
    # Test 3 points with a consecutive duplicate
    [(38.142233, -76.434082, 300),
     (38.141878, -76.425198, 700),
     (38.141878, -76.425198, 700),
     (38.144599, -76.428186, 100)],
    # Test 4 points
    [(38.145574, -76.428492, 100),
     (38.149164, -76.427113, 750),
     (38.148662, -76.431517, 300),
     (38.146143, -76.426727, 500)],
    # Test 5 points
    [(38.145405, -76.428310, 100),
     (38.146582, -76.424099, 200),
     (38.144662, -76.427634, 300),
     (38.147729, -76.419185, 200),
     (38.147573, -76.420832, 100),
     (38.148522, -76.419507, 750)]
]  # yapf: disable

TESTDATA_MOVOBST_EVALCOLLISION = (
    # Obst radius and speed
    100, 200,
    # Positions (lat, lon, alt)
    [(38, -76, 100),
     (38.1, -76.1, 200)],
    # Time, Inside pos, outside pos
    [(0.0,
      [(38, -76, 100),
       (38, -76, 0),
       (38, -76, 200),
       (38.0001, -76, 100),
       (38, -76.0001, 100)],
      [(38.1, -76.1, 200),
       (38.1, -76.1, 100),
       (38.1, -76.1, 300),
       (38.002, -76.002, 100),
       (38, -76, 201),
       (38, -76, -1)]),
     (137.526986,
      [(38.1, -76.1, 200),
       (38.1, -76.1, 225),
       (38.1, -76.1, 175)],
      [(38, -76, 100),
       (38.1, -76.1, 350),
       (38.1, -76.1, 50)])
     ]
)  # yapf: disable


class TestMovingObstacle(TestCase):
    """Tests the MovingObstacle model."""

    def setUp(self):
        """Create the obstacles for testing."""
        # Obstacle with no waypoints
        obst_no_wpt = MovingObstacle()
        obst_no_wpt.speed_avg = 1
        obst_no_wpt.sphere_radius = 1
        obst_no_wpt.save()
        self.obst_no_wpt = obst_no_wpt

        # Obstacle with single waypoint
        self.single_wpt_lat = 40
        self.single_wpt_lon = 76
        self.single_wpt_alt = 100
        obst_single_wpt = MovingObstacle()
        obst_single_wpt.speed_avg = 1
        obst_single_wpt.sphere_radius = 1
        obst_single_wpt.save()
        single_gpos = GpsPosition()
        single_gpos.latitude = self.single_wpt_lat
        single_gpos.longitude = self.single_wpt_lon
        single_gpos.save()
        single_apos = AerialPosition()
        single_apos.gps_position = single_gpos
        single_apos.altitude_msl = self.single_wpt_alt
        single_apos.save()
        single_wpt = Waypoint()
        single_wpt.position = single_apos
        single_wpt.order = 1
        single_wpt.save()
        obst_single_wpt.waypoints.add(single_wpt)
        self.obst_single_wpt = obst_single_wpt

        # Obstacles with predefined path
        self.obstacles = []
        for path in TESTDATA_MOVOBST_PATHS:
            cur_obst = MovingObstacle()
            cur_obst.speed_avg = 68
            cur_obst.sphere_radius = 10
            cur_obst.save()
            for pt_id in range(len(path)):
                (lat, lon, alt) = path[pt_id]
                cur_gpos = GpsPosition()
                cur_gpos.latitude = lat
                cur_gpos.longitude = lon
                cur_gpos.save()
                cur_apos = AerialPosition()
                cur_apos.gps_position = cur_gpos
                cur_apos.altitude_msl = alt
                cur_apos.save()
                cur_wpt = Waypoint()
                cur_wpt.position = cur_apos
                cur_wpt.order = pt_id
                cur_wpt.save()
                cur_obst.waypoints.add(cur_wpt)
            cur_obst.save()
            self.obstacles.append(cur_obst)

    def test_unicode(self):
        """Tests the unicode method executes."""
        obst = MovingObstacle()
        obst.speed_avg = 10
        obst.sphere_radius = 100
        obst.save()
        for _ in range(3):
            pos = GpsPosition()
            pos.latitude = 10
            pos.longitude = 100
            pos.save()
            apos = AerialPosition()
            apos.altitude_msl = 1000
            apos.gps_position = pos
            apos.save()
            wpt = Waypoint()
            wpt.position = apos
            wpt.order = 10
            wpt.save()
            obst.waypoints.add(wpt)
        self.assertTrue(obst.__unicode__())

    def test_get_waypoint_travel_time_invalid_inputs(self):
        """Tests proper invalid input handling."""
        obstacle = MovingObstacle()
        obstacle.speed_avg = 1

        self.assertIsNone(obstacle.get_waypoint_travel_time(None, 1, 1))
        self.assertIsNone(obstacle.get_waypoint_travel_time([], 1, 1))
        self.assertIsNone(obstacle.get_waypoint_travel_time([None], 1, 1))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], None, 1))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], 1, None))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], -1, 0))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], 0, -1))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], 2, 0))
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], 0, 2))
        obstacle.speed_avg = 0
        self.assertIsNone(obstacle.get_waypoint_travel_time(
            [None, None], 0, 1))

    def eval_travel_time(self, time_actual, time_received):
        """Evaluates whether the travel times are close enough."""
        EVAL_THRESH = time_actual * 0.1
        return abs(time_actual - time_received) < EVAL_THRESH

    def test_get_waypoint_travel_time(self):
        """Tests travel time calc."""
        test_spds = [1, 10, 100, 500]
        for (lon2, lat2, lon1, lat1, dist_km) in TESTDATA_COMPETITION_DIST:
            dist_ft = units.kilometers_to_feet(dist_km)
            for speed in test_spds:
                speed_fps = units.knots_to_feet_per_second(speed)
                time = dist_ft / speed_fps
                gpos1 = GpsPosition()
                gpos1.latitude = lat1
                gpos1.longitude = lon1
                gpos1.save()
                apos1 = AerialPosition()
                apos1.gps_position = gpos1
                apos1.altitude_msl = 0
                apos1.save()
                wpt1 = Waypoint()
                wpt1.position = apos1
                gpos2 = GpsPosition()
                gpos2.latitude = lat2
                gpos2.longitude = lon2
                gpos2.save()
                apos2 = AerialPosition()
                apos2.gps_position = gpos2
                apos2.altitude_msl = 0
                apos2.save()
                wpt2 = Waypoint()
                wpt2.position = apos2
                waypoints = [wpt1, wpt2]
                obstacle = MovingObstacle()
                obstacle.speed_avg = speed
                self.assertTrue(self.eval_travel_time(
                    obstacle.get_waypoint_travel_time(waypoints, 0, 1), time))

    def test_get_position_no_waypoints(self):
        """Tests position calc on no-"""
        self.assertEqual(self.obst_no_wpt.get_position(), (0, 0, 0))

    def test_get_position_one_waypoint(self):
        """Tests position calc on single waypoints."""
        (lat, lon, alt) = self.obst_single_wpt.get_position()
        self.assertEqual(lat, self.single_wpt_lat)
        self.assertEqual(lon, self.single_wpt_lon)
        self.assertEqual(alt, self.single_wpt_alt)

    def test_get_position_changes(self):
        """Position of obstacle changes over time."""
        # Pick an obstacle with more than one point
        obstacle = self.obstacles[0]

        original = obstacle.get_position()
        time.sleep(0.1)
        new = obstacle.get_position()

        self.assertNotEqual(original, new)

    def test_get_position_waypoints_plot(self):
        """Tests position calculation by saving plots of calculation.

        Saves plots to test_output/auvsi_suas-MovingObstacle-getPosition-x.jpg.
        On each run it first deletes the existing folder. This requires manual
        inspection to validate correctness.
        """
        if not settings.TEST_ENABLE_PLOTTING:
            return

        # Create directory for plot output
        if not os.path.exists('data'):
            os.mkdir('data')
        if os.path.exists('data/test_output'):
            shutil.rmtree('data/test_output')
        os.mkdir('data/test_output')

        # Create plot for each path
        for obst_id in range(len(self.obstacles)):
            cur_obst = self.obstacles[obst_id]

            # Get waypoint positions as numpy array
            waypoints = cur_obst.waypoints.order_by('order')
            waypoint_travel_times = cur_obst.get_inter_waypoint_travel_times(
                waypoints)
            waypoint_times = cur_obst.get_waypoint_times(waypoint_travel_times)
            total_time = waypoint_times[len(waypoint_times) - 1]
            num_waypoints = len(waypoints)
            wpt_latitudes = np.zeros(num_waypoints + 1)
            wpt_longitudes = np.zeros(num_waypoints + 1)
            wpt_altitudes = np.zeros(num_waypoints + 1)
            for waypoint_id in range(num_waypoints + 1):
                cur_id = waypoint_id % num_waypoints

                # yapf: disable
                wpt_latitudes[waypoint_id] = waypoints[cur_id].position.latitude
                wpt_longitudes[waypoint_id] = waypoints[cur_id].position.longitude
                wpt_altitudes[waypoint_id] = waypoints[cur_id].position.altitude_msl
                # yapf: enable

                # Create time series to represent samples at 10 Hz for 1.5 trips
            time_pos = np.arange(0, 1.5 * total_time, 0.10)
            # Sample position for the time series
            latitudes = np.zeros(len(time_pos))
            longitudes = np.zeros(len(time_pos))
            altitudes = np.zeros(len(time_pos))
            epoch = timezone.now().replace(year=1970,
                                           month=1,
                                           day=1,
                                           hour=0,
                                           minute=0,
                                           second=0,
                                           microsecond=0)
            for time_id in range(len(time_pos)):
                cur_time_offset = time_pos[time_id]
                cur_samp_time = epoch + datetime.timedelta(
                    seconds=cur_time_offset)

                (lat, lon, alt) = cur_obst.get_position(cur_samp_time)
                latitudes[time_id] = lat
                longitudes[time_id] = lon
                altitudes[time_id] = alt

            # Create plot
            plt.figure()
            plt.subplot(311)
            plt.plot(time_pos, latitudes, 'b', waypoint_times, wpt_latitudes,
                     'rx')
            plt.subplot(312)
            plt.plot(time_pos, longitudes, 'b', waypoint_times, wpt_longitudes,
                     'rx')
            plt.subplot(313)
            plt.plot(time_pos, altitudes, 'b', waypoint_times, wpt_altitudes,
                     'rx')
            plt.savefig(
                ('data/test_output/'
                 'auvsi_suas-MovingObstacle-getPosition-%d.jpg' % obst_id))

    def test_contains_pos(self):
        """Tests the inside obstacle method."""
        # Form the test obstacle
        obst = MovingObstacle()
        obst.sphere_radius = TESTDATA_MOVOBST_CONTAINSPOS_OBJ[2]
        # Run test points against obstacle
        test_data = [
            (TESTDATA_MOVOBST_CONTAINSPOS_INSIDE, True),
            (TESTDATA_MOVOBST_CONTAINSPOS_OUTSIDE, False)
        ]
        for (cur_data, cur_contains) in test_data:
            for (lat, lon, alt) in cur_data:
                gpos = GpsPosition()
                gpos.latitude = lat
                gpos.longitude = lon
                gpos.save()
                apos = AerialPosition()
                apos.gps_position = gpos
                apos.altitude_msl = alt
                self.assertEqual(
                    obst.contains_pos(TESTDATA_MOVOBST_CONTAINSPOS_OBJ[0],
                                      TESTDATA_MOVOBST_CONTAINSPOS_OBJ[1],
                                      TESTDATA_MOVOBST_CONTAINSPOS_OBJ[3],
                                      apos), cur_contains)

    def test_evaluate_collision_with_uas(self):
        """Tests the collision with UAS method."""
        # Get test data
        user = User.objects.create_user('testuser', 'testemail@x.com',
                                        'testpass')
        user.save()
        testdata = TESTDATA_MOVOBST_EVALCOLLISION
        (obst_rad, obst_speed, obst_pos, log_details) = testdata
        # Create the obstacle
        obst = MovingObstacle()
        obst.speed_avg = obst_speed
        obst.sphere_radius = obst_rad
        obst.save()
        for pos_id in xrange(len(obst_pos)):
            (lat, lon, alt) = obst_pos[pos_id]
            gpos = GpsPosition()
            gpos.latitude = lat
            gpos.longitude = lon
            gpos.save()
            apos = AerialPosition()
            apos.gps_position = gpos
            apos.altitude_msl = alt
            apos.save()
            wpt = Waypoint()
            wpt.order = pos_id
            wpt.position = apos
            wpt.save()
            obst.waypoints.add(wpt)
        obst.save()
        # Create sets of logs
        epoch = timezone.now().replace(year=1970,
                                       month=1,
                                       day=1,
                                       hour=0,
                                       minute=0,
                                       second=0,
                                       microsecond=0)
        inside_logs = []
        outside_logs = []
        for (time_sec, inside_pos, outside_pos) in log_details:
            log_time = epoch + datetime.timedelta(seconds=time_sec)
            logs_pos = [(inside_pos, inside_logs), (outside_pos, outside_logs)]
            for (positions, log_list) in logs_pos:
                for (lat, lon, alt) in positions:
                    gpos = GpsPosition()
                    gpos.latitude = lat
                    gpos.longitude = lon
                    gpos.save()
                    apos = AerialPosition()
                    apos.gps_position = gpos
                    apos.altitude_msl = alt
                    apos.save()
                    log = UasTelemetry()
                    log.user = user
                    log.uas_position = apos
                    log.uas_heading = 0
                    log.save()
                    log.timestamp = log_time
                    log.save()
                    log_list.append(log)

        # Assert the obstacle correctly computes collisions
        log_collisions = [(True, inside_logs), (False, outside_logs)]
        for (inside, logs) in log_collisions:
            self.assertEqual(obst.evaluate_collision_with_uas(logs), inside)
            for log in logs:
                self.assertEqual(
                    obst.evaluate_collision_with_uas([log]), inside)

    def test_json(self):
        """Tests the JSON serialization method."""
        for cur_obst in self.obstacles:
            json_data = cur_obst.json()
            self.assertTrue('latitude' in json_data)
            self.assertTrue('longitude' in json_data)
            self.assertTrue('altitude_msl' in json_data)
            self.assertTrue('sphere_radius' in json_data)
            self.assertEqual(json_data['sphere_radius'],
                             cur_obst.sphere_radius)
        obst = self.obst_single_wpt
        json_data = obst.json()

        # yapf: disable
        self.assertEqual(json_data['latitude'],
                         obst.waypoints.all()[0].position.gps_position.latitude)
        self.assertEqual(json_data['longitude'],
                         obst.waypoints.all()[0].position.gps_position.longitude)
        self.assertEqual(json_data['altitude_msl'],
                         obst.waypoints.all()[0].position.altitude_msl)
        # yapf: enable

    def test_kml(self):
        """
        Tests the generation of kml data
            The correct number of elements are generated
            The meta-data tag is present
        """
        array_field_tag = '<gx:SimpleArrayField name="proximity" type="float">'
        coordinates = [
            (-76.0, 38.0, 0.0),
            (-76.0, 38.0, 10.0),
            (-76.0, 38.0, 20.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 100.0),
            (-76.0, 38.0, 30.0),
            (-76.0, 38.0, 60.0),
        ]

        user = User.objects.create_user('testuser', 'testemail@x.com',
                                        'testpass')
        user.save()

        # Create Coordinates
        start_time = timezone.now()
        next_time = start_time
        end_time = start_time
        for coord in coordinates:
            self.create_log_element(*coord, user=user, log_time=next_time)
            end_time = next_time
            next_time += datetime.timedelta(seconds=1)

        # Calculate expected number of data tags
        time_delta = end_time - start_time
        ms_elapsed = time_delta.total_seconds() * 1000
        kml_output_resolution = 100  # milliseconds
        samples_expected = int(ms_elapsed / kml_output_resolution)

        for cur_obst in self.obstacles:
            kml = Kml()
            kml_mission = kml.newfolder(name='SubFolder')
            cur_obst.kml(path=UasTelemetry.by_user(user),
                         kml=kml_mission,
                         kml_doc=kml.document)
            result_kml = kml.kml()
            self.assertEqual(samples_expected, result_kml.count('<gx:value>'))
            self.assertIn(array_field_tag, result_kml)

    def create_log_element(self, lat, lon, alt, user, log_time):
        pos = GpsPosition(latitude=lat, longitude=lon)
        pos.save()
        apos = AerialPosition(gps_position=pos, altitude_msl=alt)
        apos.save()
        log = UasTelemetry(user=user, uas_position=apos, uas_heading=100, )
        log.save()
        log.timestamp = log_time
        log.save()
        return log

    def test_json_time_changes(self):
        """json, called at different times, causes different locations"""
        for o in self.obstacles:
            d1 = o.json()
            d2 = o.json()
            self.assertNotEqual(d1, d2)

    def test_json_time_freeze(self):
        """json, called at the same time, causes same locations"""
        time = timezone.now()

        for o in self.obstacles:
            d1 = o.json(time=time)
            d2 = o.json(time=time)
            self.assertEqual(d1, d2)
