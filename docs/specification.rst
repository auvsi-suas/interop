Interface Specification
=======================

This section describes the interoperability interface that is
implemented by the AUVSI SUAS competition server. Teams should use this
documentation to integrate with the competition server.

Hostname & Port
---------------

The competition will specify the hostname and port during the competition.
Teams will not have this during the development and testing period. For testing
purposes, teams can use the provided competition server to evaluate their
system. The hostname will be the IP address of the computer on which the server
is running, and the port will be the port selected when starting the server.
Teams must be able to specify this to their system during the mission. The
hostname can also be the hostname given to the computer. The hostname
"localhost" is a reserved name for the local host, and it resolves to the
loopback IP address 127.0.0.1. An example hostname and port combination is
"192.168.1.2:8080".

Relative URLs
-------------

The relative URLs (endpoints) are described further in the following sections.
The interface defined in this document is what will be used at the competition.
Only slight changes may be made leading up to the competition to fix bugs or
add features. Teams should synchronize their code and check this documentation
for updates. An example relative URL is ``/api/server_info``.

Full Resource URL
-----------------

The full resource URL is the combination of the hostname, port, and relative
URL. This is the URL that must be used to make requests. An example full
resource URL is "http://192.168.1.2:80/api/login".

Endpoints
---------

Below are all of the endpoints provided by the server, displayed by their
relative URL, and the HTTP method with which you access them.

A quick summary of the endpoints:

* :http:post:`/api/login`: Used to authenticate with the competition server so
  that future requests will be authenticated. Teams cannot make other requests
  without logging in successfully.

* :http:get:`/api/missions`: Used to get details for available missions.

* :http:get:`/api/missions/(int:id)`: Used to get details for a mission.

* :http:get:`/api/obstacles`: Used to download
  obstacle information from the competition server for purpose of
  displaying it and avoiding the obstacles.

* :http:post:`/api/telemetry`: Used to upload UAS telemetry information
  to the competition server. Uploading telemetry to this endpoint is
  required by the competition rules.

* :http:post:`/api/targets`: Used to upload targets for submission.

* :http:get:`/api/targets`: Used to retrieve targets uploaded for submission.

* :http:get:`/api/targets/(int:id)`: Used to get details about submitted
  targets.

* :http:put:`/api/targets/(int:id)`: Used to update characteristics of
  submitted targets.

* :http:delete:`/api/targets/(int:id)`: Used to delete a submitted target.

* :http:get:`/api/targets/(int:id)/image`: Used to get target image previously
  submitted.

* :http:post:`/api/targets/(int:id)/image`: Used to submit or update target
  image thumbnail.

* :http:delete:`/api/targets/(int:id)/image`: Used to delete target image
  thumbnail.

Errors
^^^^^^

Some of the HTTP request errors you may receive when using this API:

* :http:statuscode:`404`: The request was made to an invalid URL, the server
  does not know how to respond to such a request.  Check the endpoint URL.

* :http:statuscode:`405`: The request used an invalid method (e.g.,
  :http:method:`GET` when only :http:method:`POST` is supported). Double check
  the documentation below for the methods supported by each endpoint.

* :http:statuscode:`500`: The server encountered an internal error and was
  unable to process the request. This indicates a configuration error on the
  server side.


User Login
^^^^^^^^^^

.. http:post:: /api/login

   Teams login to the competition server by making an HTTP POST request with
   two parameters: "username" and "password". Teams only need to make a login
   once before any other requests. The login request, if successful, will
   return cookies that uniquely identify the user and the current session.
   Teams must send these cookies to the competition server in all future
   requests.

   **Example Request**:

   .. sourcecode:: http

      POST /api/login HTTP/1.1
      Host: 192.168.1.2:8000
      Content-Type: application/x-www-form-urlencoded

      username=testadmin&password=testpass

   **Example Response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Set-Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi; expires=Mon, 17-Aug-2015 02:41:09 GMT; httponly; Max-Age=1209600; Path=/

      Login Successful.

   :form username: This parameter is the username that the judges give teams
                   during the competition. This is a unique identifier that
                   will be used to associate the requests as your team's.

   :form password: This parameter is the password that the judges give teams
                   during the competition. This is used to ensure that teams
                   do not try to spoof other team's usernames, and that
                   requests are authenticated with security.

   :resheader Set-Cookie: Upon successful login, a session cookie will be sent
                          back to the client. This cookie must be sent with
                          each subsequent request, authenticating the request.

   :status 200: Successful logins will have a response status code of 200.
                The content of the response will be a success message. The
                response will also include cookies which must be sent with
                future requests.

   :status 400: Unsuccessful logins will have a response status code of
                400. The content of the response will be an error message
                indicating why the request failed. Requests can fail because
                the request was missing one of the required parameters, or
                had invalid login information.


Missions
^^^^^^^^

.. http:get:: /api/missions

   This endpoint is used to retrieve a list of available missions and details.

   **Example Request**:

   .. sourcecode:: http

      GET /api/missions HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example Response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "id": 1,
              "active": true,
              "air_drop_pos": {
                  "latitude": 38.141833,
                  "longitude": -76.425263
              },
              "fly_zones": [
                  {
                      "altitude_msl_max": 200.0,
                      "altitude_msl_min": 100.0,
                      "boundary_pts": [
                          {
                              "latitude": 38.142544,
                              "longitude": -76.434088,
                              "order": 1
                          },
                          {
                              "latitude": 38.141833,
                              "longitude": -76.425263,
                              "order": 2
                          },
                          {
                              "latitude": 38.144678,
                              "longitude": -76.427995,
                              "order": 3
                          }
                      ]
                  }
              ],
              "home_pos": {
                  "latitude": 38.14792,
                  "longitude": -76.427995
              },
              "mission_waypoints": [
                  {
                      "altitude_msl": 200.0,
                      "latitude": 38.142544,
                      "longitude": -76.434088,
                      "order": 1
                  }
              ],
              "off_axis_target_pos": {
                  "latitude": 38.142544,
                  "longitude": -76.434088
              },
              "emergent_last_known_pos": {
                  "latitude": 38.145823,
                  "longitude": -76.422396
              },
              "search_grid_points": [
                  {
                      "altitude_msl": 200.0,
                      "latitude": 38.142544,
                      "longitude": -76.434088,
                      "order": 1
                  }
              ]
          }
      ]


   The response format is a list of mission objects. Each is in the same as
   :http:get:`/api/missions/(int:id)` and is described in detail there.

   If no missions have been created, the response will contain an empty list.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: The response is ``application/json`` on success.

   :status 200: Success. Response contains missions.

   :status 403: User not authenticated. Login is required before using this
                endpoint.  Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

.. http:get:: /api/missions/(int:id)

   This endpoint gets the details about a mission with id ``id``.

   **Example request**:

   .. sourcecode:: http

      GET /api/missions/1 HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "id": 1,
          "active": true,
          "air_drop_pos": {
              "latitude": 38.141833,
              "longitude": -76.425263
          },
          "fly_zones": [
              {
                  "altitude_msl_max": 200.0,
                  "altitude_msl_min": 100.0,
                  "boundary_pts": [
                      {
                          "latitude": 38.142544,
                          "longitude": -76.434088,
                          "order": 1
                      },
                      {
                          "latitude": 38.141833,
                          "longitude": -76.425263,
                          "order": 2
                      },
                      {
                          "latitude": 38.144678,
                          "longitude": -76.427995,
                          "order": 3
                      }
                  ]
              }
          ],
          "home_pos": {
              "latitude": 38.14792,
              "longitude": -76.427995
          },
          "mission_waypoints": [
              {
                  "altitude_msl": 200.0,
                  "latitude": 38.142544,
                  "longitude": -76.434088,
                  "order": 1
              }
          ],
          "off_axis_target_pos": {
              "latitude": 38.142544,
              "longitude": -76.434088
          },
          "emergent_last_known_pos": {
              "latitude": 38.145823,
              "longitude": -76.422396
          },
          "search_grid_points": [
              {
                  "altitude_msl": 200.0,
                  "latitude": 38.142544,
                  "longitude": -76.434088,
                  "order": 1
              }
          ]
      }


   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: The response is ``application/json`` on success.

   :>json int id: Unique identifier for this mission.

   :>json boolean active: Whether the mission is active. Only a single mission
                          should be active, and it should be the mission the
                          team is interacting with.

   :>json object air_drop_pos: The position of the air drop.

   :>json array fly_zones: A list of fly_zone boundaries. The UAS must be within
                           one of these boundaries at all times. A single
                           boundary consists of a GPS polygon and an altitude
                           range. The UAS is within the boundary if it is both
                           inside the polygon and the altitude range.

   :>json float altitude_msl_min: (member of ``fly_zones``) The minimum
                                  altitude in feet MSL.

   :>json float altitude_msl_max: (member of ``fly_zones``) The maximum
                                  altitude in feet MSL.

   :>json array boundary_pts: (member of ``fly_zones``) A list of waypoints
                              defining a polygon.

   :>json object home_pos: The launch point of the UAVs (flight-line tents).

   :>json array mission_waypoints: A list of waypoints the UAS must traverse.

   :>json object off_axis_target_pos: The GPS position of the off-axis target.

   :>json object emergent_last_known_pos: The last known GPS position of the
                                          emergent target.

   :>json array search_grid_points: A list of waypoints defining the search
                                    grid polygon.

   :>json object gps_position: (Type for ``air_drop_ops``, ``home_pos``,
                               ``off_axis_target_pos``)
                               Consists of a latitude and longitude.

   :>json object waypoint: (Type for ``boundary_pts``, ``mission_waypoints``,
                           and ``search_grid_points``) Consists of a order
                           number (relative ordering between set of waypoints),
                           latitude, longitude, and optional altitude.

   :>json float latitude: (Member of ``gps_position`` and ``waypoint``)
                          Latitude in decimal degrees.

   :>json float longitude: (Member of ``gps_position`` and ``waypoint``)
                           Longitude in decimal degrees.

   :>json float altitude_msl: (Member of ``waypoint``) Altitude in feet MSL.

   :status 200: Success. Response contains mission details.

   :status 403: User not authenticated. Login is required before using this
                endpoint. Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

   :status 404: Mission not found. Check ID.


Obstacle Information
^^^^^^^^^^^^^^^^^^^^

.. http:get:: /api/obstacles

   Teams make requests to obtain obstacle information for purpose of displaying
   the information and for avoiding the obstacles. This request is a GET
   request with no parameters. The data returned will be in JSON format.

   **Example Request**:

   .. sourcecode:: http

      GET /api/obstacles HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example Response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "moving_obstacles": [
              {
                  "altitude_msl": 189.56748784643966,
                  "latitude": 38.141826869853645,
                  "longitude": -76.43199876559223,
                  "sphere_radius": 150.0
              },
              {
                  "altitude_msl": 250.0,
                  "latitude": 38.14923628783763,
                  "longitude": -76.43238529543882,
                  "sphere_radius": 150.0
              }
          ],
          "stationary_obstacles": [
              {
                  "cylinder_height": 750.0,
                  "cylinder_radius": 300.0,
                  "latitude": 38.140578,
                  "longitude": -76.428997
              },
              {
                  "cylinder_height": 400.0,
                  "cylinder_radius": 100.0,
                  "latitude": 38.149156,
                  "longitude": -76.430622
              }
          ]
      }

   **Note**: The ``stationary_obstacles`` and ``moving_obstacles`` fields are
   lists. This means that there can be 0, 1, or many objects contained
   within each list. Above shows an example with 2 moving obstacles and 2
   stationary obstacles.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: The response is ``application/json`` on success.

   :>json array moving_obstacles: List of zero or more moving obstacles.

   :>json array stationary_obstacles: List of zero or more stationary obstacles.

   :>json float latitude: (member of object in ``moving_obstacles`` or
                          ``stationary_obstacles``) The obstacle's current
                          altitude in degrees.

   :>json float longitude: (member of object in ``moving_obstacles`` or
                           ``stationary_obstacles``) The obstacle's current
                           longitude in degrees.

   :>json float altitude_msl: (member of object in ``moving_obstacles``) The
                              moving obstacle's current centroid altitude in
                              feet MSL.

   :>json float sphere_radius: (member of object in ``moving_obstacles``) The
                               moving obstacle's radius in feet.

   :>json float cylinder_radius: (member of object in ``stationary_obstacles``)
                                 The stationary obstacle's radius in feet.

   :>json float cylinder_height: (member of object in ``stationary_obstacles``)
                                 The stationary obstacle's height in feet.

   :status 200: The team made a valid request. The request will be logged to
                later evaluate request rates. The response will have status
                code 200 to indicate success, and it will have content in JSON
                format. This JSON data is the server information that teams
                must display, and it contains data which can be used to avoid
                the obstacles. The format for the JSON data is given below.

   :status 403: User not authenticated. Login is required before using this
                endpoint. Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

UAS Telemetry
^^^^^^^^^^^^^

.. http:post:: /api/telemetry

   Teams make requests to upload the UAS telemetry to the competition server.
   The request is a POST request with parameters ``latitude``, ``longitude``,
   ``altitude_msl``, and ``uas_heading``.

   Each telemetry request should contain unique telemetry data. Duplicated
   data will be accepted but not evaluated.

   **Example Request**:

   .. sourcecode:: http

      POST /api/telemetry HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
      Content-Type: application/x-www-form-urlencoded

      latitude=38.149&longitude=-76.432&altitude_msl=100&uas_heading=90

   **Example Response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

      UAS Telemetry Successfully Posted.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :form latitude: The latitude of the aircraft as a floating point degree
                   value. Valid values are: -90 <= latitude <= 90.

   :form longitude: The longitude of the aircraft as a floating point degree
                    value. Valid values are: -180 <= longitude <= 180.

   :form altitude\_msl: The height above mean sea level (MSL) of the aircraft
                        in feet as a floating point value.

   :form uas\_heading: The (true north) heading of the aircraft as a floating point
                       degree value. Valid values are: 0 <= uas\_heading <= 360.

   :status 200: The team made a valid request. The information will be stored
                on the competition server to evaluate various competition
                rules. The content of the response will have a success
                message.

   :status 400: Invalid requests will return a response code of 400. A request
                will be invalid if the user did not specify a parameter, or
                if the user specified an invalid value for a parameter. The
                content of the response will have an error message indicating
                what went wrong.

   :status 403: User not authenticated. Login is required before using this
                endpoint. Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

Targets
^^^^^^^

.. http:post:: /api/targets

   This endpoint is used to upload a new target for submission. All targets
   uploaded at the end of the mission time will be evaluated by the judges.

   Most of the target characteristics are optional; if not provided in this
   initial POST request, they may be added in a future PUT request.
   Characteristics not provided will be considered left blank. Note that some
   characteristics must be submitted by the end of the mission to earn credit
   for the target.

   The fields that should be used depends on the type of target being submitted.
   Refer to :py:data:`TargetTypes` for more detail.

   **Example Request**:

   .. sourcecode:: http

      POST /api/targets HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
      Content-Type: application/json

      {
          "type": "standard",
          "latitude": 38.1478,
          "longitude": -76.4275,
          "orientation": "n",
          "shape": "star",
          "background_color": "orange",
          "alphanumeric": "C",
          "alphanumeric_color": "black"
      }

   **Example Response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 201 CREATED
      Content-Type: application/json

      {
          "id": 1,
          "user": 1,
          "type": "standard",
          "latitude": 38.1478,
          "longitude": -76.4275,
          "orientation": "n",
          "shape": "star",
          "background_color": "orange",
          "alphanumeric": "C",
          "alphanumeric_color": "black",
          "description": null,
          "autonomous": false
      }

   The response format is the same as :http:get:`/api/targets/(int:id)` and
   is described in detail there.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :reqheader Content-Type: The request should be sent as ``application/json``.

   :<json string type: (required) Target type; must be one of
                       :py:data:`TargetTypes`.

   :<json float latitude: (optional) Target latitude (decimal degrees). If
                          ``latitude`` is provided, ``longitude`` must also be
                          provided.

   :<json float longitude: (optional) Target longitude (decimal degrees). If
                          ``longitude`` is provided, ``latitude`` must also be
                          provided.

   :<json string orientation: (optional) Target orientation; must be one of
                              :py:data:`Orientations`.

   :<json string shape: (optional) Target shape; must be one of
                        :py:data:`Shapes`.

   :<json string background_color: (optional) Target background color (portion
                                   of the target outside the alphanumeric); must
                                   be one of :py:data:`Colors`.

   :<json string alphanumeric: (optional) Target alphanumeric; may consist of
                               one or more of the characters ``0-9``, ``A-Z``,
                               ``a-z``. It is case sensitive.

   :<json string alphanumeric_color: (optional) Target alphanumeric color; must be
                                     one of :py:data:`Colors`.

   :<json string description: (optional) Free-form description of target. This
                              should be used for describing certain target
                              types (see :py:data:`TargetTypes`).

   :<json boolean autonomous: (optional, default ``false``) This target was
                              detected, localized, and characterized by the
                              team's ADLC system, per section 7.3 of the
                              rules. Note that if this field is set, then
                              detection, localization, and characterization
                              must be autonomous, with no human input. Per
                              section 7.3 of the rules, no more than six
                              targets should be marked autonomous.

   :resheader Content-Type: The response is ``application/json`` on success.

   :status 201: The target has been accepted and a record has been created for
                it. The record has been included in the response.

   :status 400: Request was invalid. The request content may have been
                malformed, missing required fields, or may have contained
                invalid field values. The response includes a more detailed
                error message.

   :status 403: User not authenticated. Login is required before using this
                endpoint. Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

.. http:get:: /api/targets

   This endpoint is used to retrieve a list of targets uploaded for submission.

   The targets returned by this endpoint are those that have been uploaded with
   :http:post:`/api/targets` and possibly updated with
   :http:put:`/api/targets/(int:id)`.

   .. note::

        This endpoint will only return up to 100 targets. It is recommended to
        remain below 100 targets total (there certainly won't be that many at
        competition!). If you do have more than 100 targets, individual targets
        may be queried with :http:get:`/api/targets/(int:id)`.

   **Example request**:

   .. sourcecode:: http

      GET /api/targets HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "id": 1,
              "user": 1,
              "type": "standard",
              "latitude": 38.1478,
              "longitude": -76.4275,
              "orientation": "n",
              "shape": "star",
              "background_color": "orange",
              "alphanumeric": "C",
              "alphanumeric_color": "black",
              "description": null,
              "autonomous": false
          },
          {
              "id": 2,
              "user": 1,
              "type": "emergent",
              "latitude": 38.1878,
              "longitude": -76.4075,
              "orientation": null,
              "shape": null,
              "background_color": null,
              "alphanumeric": null,
              "alphanumeric_color": null,
              "description": "Firefighter fighting a fire.",
              "autonomous": false
          }
      ]

   The response format is a list of target objects. Each is in the same as
   :http:get:`/api/targets/(int:id)` and is described in detail there.

   If no targets have been uploaded, the response will contain an empty list.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: The response is ``application/json`` on success.

   :status 200: Success. Response contains targets.

   :status 403: User not authenticated. Login is required before using this
                endpoint.  Ensure :http:post:`/api/login` was successful, and
                the login cookie was sent to this endpoint.

.. http:get:: /api/targets/(int:id)

   Details about a target id ``id``. This simple endpoint allows you to verify
   the uploaded characteristics of a target.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. When you first upload your target to
   :http:post:`/api/targets`, the response includes an ``id`` field, whose value
   you use to access this endpoint. Note that this id is unique to all teams
   and will not necessarily start at 1 or increase linearly with additional
   targets.

   **Example request**:

   .. sourcecode:: http

      GET /api/targets/1 HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "id": 1,
          "user": 1,
          "type": "standard",
          "latitude": 38.1478,
          "longitude": -76.4275,
          "orientation": "n",
          "shape": "star",
          "background_color": "orange",
          "alphanumeric": "C",
          "alphanumeric_color": "black",
          "description": null,
          "autonomous": false
      }

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: The response is ``application/json`` on success.

   :>json int id: Unique identifier for this target. This is unique across
                  all teams, it may not naturally increment 1-10. Used to
                  reference specific targets in various endpoints. The target
                  ID does not change when a target is updated.

   :>json int user: Unique identifier for the team. Teams should not need to
                    use this field.

   :>json string type: Target type; one of :py:data:`TargetTypes`.

   :>json float latitude: Target latitude in decimal degrees,  or ``null`` if
                          no latitude specified yet.

   :>json float longitude: Target longitude in decimal degrees,  or ``null`` if
                          no longitude specified yet.

   :>json string orientation: Target orientation; one of :py:data:`Orientations`,
                              or ``null`` if no orientation specified yet.

   :>json string shape: Target shape; one of :py:data:`Shapes`, or ``null`` if no
                        shape specified yet.

   :>json string background_color: Target background color; one of
                                   :py:data:`Colors`, or ``null`` if no
                                   background color specified yet.

   :>json string alphanumeric: Target alphanumeric; ``null`` if no alphanumeric
                               specified yet.

   :>json string alphanumeric_color: Target alphanumeric color; one of
                                     :py:data:`Colors`, or ``null`` if no
                                     alphanumeric color specified yet.

   :>json string description: Target description; ``null`` if no description
                              specified yet.

   :>json boolean autonomous: Target is an ADLC target.

   :status 200: Success. Response contains target details.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: Target not found. Check target ID.

.. http:put:: /api/targets/(int:id)

   Update target id ``id``. This endpoint allows you to specify characteristics
   that were omitted in :http:post:`/api/targets`, or update those that were
   specified.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. See :http:get:`/api/targets/(int:id)` for more
   information about the target ID.

   **Example request**:

   .. sourcecode:: http

      PUT /api/targets/1 HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
      Content-Type: application/json

      {
          "alphanumeric": "O"
      }

   **Example response**:

   Note: This example reformatted for readability; actual response may be
   entirely on one line.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "id": 1,
          "user": 1,
          "type": "standard",
          "latitude": 38.1478,
          "longitude": -76.4275,
          "orientation": "n",
          "shape": "star",
          "background_color": "orange",
          "alphanumeric": "O",
          "alphanumeric_color": "black",
          "description": null,
          "autonomous": false
      }

   This endpoint accepts all fields described in :http:post:`/api/targets` in
   its request. Any fields that are specified will be updated, overwriting the
   old value. Any fields omitted will not be changed. Specifying a field with
   a ``null`` value will clear that field (except ``type``, which may never be
   ``null``).

   In the example above, only the ``alphanumeric`` field was sent to in the
   request. As can be seen in the response, the ``alphanumeric`` field has
   the new value, but all other fields have been left unchanged.

   The response format is the same as :http:get:`/api/targets/(int:id)` and
   is described in detail there.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :reqheader Content-Type: The request should be sent as ``application/json``.

   :resheader Content-Type: The response is ``application/json`` on success.

   :status 200: The target has been successfully updated, and the updated
                target is included in the response.

   :status 400: Request was invalid. The request content may have been
                malformed or it may have contained invalid field values. The
                response includes a more detailed error message.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: Target not found. Check target ID.

.. http:delete:: /api/targets/(int:id)

   Delete target id ``id``. This endpoint allows you to remove a target from
   the server entirely (including its image). Targets deleted with this
   endpoint will not be scored, and cannot be recovered. If a target is deleted
   accidentally, reupload it as a new target.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. See :http:get:`/api/targets/(int:id)` for more
   information about the target ID.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/targets/1 HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   .. FIXME(sphinx-doc/sphinx#2280): The Content-Type here is not particularly
      relevant, but otherwise the sourcecode block will fail to lex.

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: text/html

      Target deleted.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :status 200: The target has been successfully deleted. It will not be
                scored.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: Target not found. Check target ID.


.. http:get:: /api/targets/(int:id)/image

   Download previously uploaded target thumbnail. This simple endpoint returns
   the target thumbnail uploaded with a
   :http:post:`/api/targets/(int:id)/image` request.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. See :http:get:`/api/targets/(int:id)` for more
   information about the target ID.

   The response content is the image content itself on success.

   **Example request**:

   .. sourcecode:: http

      GET /api/targets/2/image HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: image/jpeg

      <binary image content ...>

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :resheader Content-Type: Matches content type of uploaded image. For
                            example, JPEG is ``image/jpeg``.

   :status 200: Target image found and included in response.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: * Target not found. Check target ID.

                * Target does not have associated image. One must first be
                  uploaded with :http:post:`/api/targets/(int:id)/image`.


.. http:post:: /api/targets/(int:id)/image

   Add or update target image thumbnail.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. See :http:get:`/api/targets/(int:id)` for more
   information about the target ID.

   This endpoint is used to submit an image of the associated target. This
   image should be a clear, close crop of the target. Subsequent calls to this
   endpoint replace the target image.

   The request body contains the raw binary content of the image. The image
   should be in either JPEG or PNG format. The request must not exceed 1 MB in
   size.

   **Example request**:

   .. sourcecode:: http

      POST /api/targets/2/image HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
      Content-Type: image/jpeg

      <binary image content ...>

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

      Image uploaded.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :reqheader Content-Type: JPEG images should be ``image/jpeg`. PNG images
                            should be ``image/png``.

   :status 200: The target image has been successfully uploaded.

   :status 400: Request was not a valid JPEG or PNG image. The response
                includes a more detailed error message.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: Target not found. Check target ID.

   :status 413: Image exceeded 1MB in size.


.. http:put:: /api/targets/(int:id)/image

   Equivalent to :http:post:`/api/targets/(int:id)/image`.

.. http:delete:: /api/targets/(int:id)/image

   Delete target image thumbnail.

   ``id`` is the unique identifier of a target, as returned by
   :http:post:`/api/targets`. See :http:get:`/api/targets/(int:id)` for more
   information about the target ID.

   This endpoint is used to delete the image associated with a target. A deleted
   image will not be used in scoring.

   .. note::

      You do not need to delete the target image before uploading a new image.
      A call to :http:post:`/api/targets/(int:id)/image` or
      :http:put:`/api/targets/(int:id)/image` will overwrite the existing
      image.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/targets/2/image HTTP/1.1
      Host: 192.168.1.2:8000
      Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

      Image deleted.

   :reqheader Cookie: The session cookie obtained from :http:post:`/api/login`
                      must be sent to authenticate the request.

   :status 200: The target image has been successfully deleted.

   :status 403: * User not authenticated. Login is required before using this
                  endpoint.  Ensure :http:post:`/api/login` was successful, and
                  the login cookie was sent to this endpoint.

                * The specified target was found but is not accessible by your
                  user (i.e., another team created this target). Check target
                  ID.

                * Check response for detailed error message.

   :status 404: * Target not found. Check target ID.

                * The specified target had no existing image to delete.


.. py:data:: TargetTypes

   These are the valid types of targets which may be specified.

   * ``standard`` - Standard targets are described in section 7.2.7 of the rules.

   Describe the target characteristics with these fields (see
   :http:post:`/api/targets`):

      * ``latitude``
      * ``longitude``
      * ``orientation``
      * ``shape``
      * ``background_color``
      * ``alphanumeric``
      * ``alphanumeric_color``
      * ``autonomous``

   * ``off_axis`` - Off-axis targets are described in section 7.5 of the rules.

   Describe the target characteristics with these fields (see
   :http:post:`/api/targets`):

      * ``orientation``
      * ``shape``
      * ``background_color``
      * ``alphanumeric``
      * ``alphanumeric_color``

   * ``emergent`` - Emergent targets are described in section 7.6 of the rules.

   Describe the target characteristics with these fields (see
   :http:post:`/api/targets`):

      * ``latitude``
      * ``longitude``
      * ``description``

         * This field should contain a general description of the emergent
           target.

.. py:data:: Orientations

   These are the valid orientations that may be specified for a target.
   They reference true north, not magnetic north.

   * ``N`` - North
   * ``NE`` - Northeast
   * ``E`` - East
   * ``SE`` - Southeast
   * ``S`` - South
   * ``SW`` - Southwest
   * ``W`` - West
   * ``NW`` - Northwest

.. py:data:: Shapes

   These are the valid shapes that may be specified for a target.

   * ``circle``
   * ``semicircle``
   * ``quarter_circle``
   * ``triangle``
   * ``square``
   * ``rectangle``
   * ``trapezoid``
   * ``pentagon``
   * ``hexagon``
   * ``heptagon``
   * ``octagon``
   * ``star``
   * ``cross``

.. py:data:: Colors

   These are the valid colors that may be specified for a target.

   * ``white``
   * ``black``
   * ``gray``
   * ``red``
   * ``blue``
   * ``green``
   * ``yellow``
   * ``purple``
   * ``brown``
   * ``orange``
