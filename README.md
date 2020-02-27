# AUVSI SUAS Interoperability

[![Build Status](https://travis-ci.com/auvsi-suas/interop.svg?branch=master)](https://travis-ci.com/auvsi-suas/interop)

Repository for the Interoperability System used in the Association for Unmanned
Vehicle Systems International (AUVSI) Student Unmanned Aerial System (SUAS)
Competition.

* [auvsi-suas.org](http://www.auvsi-suas.org/). Rules and other competition
  resources.
* [auvsi-suas@googlegroups.com](https://groups.google.com/forum/#!forum/auvsi-suas).
  Contact the competition directors and developers.
* Teams should
  [watch the repository](https://help.github.com/articles/watching-repositories/)
  so they receive notifications when things change.

Repository Contents:

* `/server`: Interoperability server, implementing the AUVSI SUAS
  Interoperability API specification.
* `/client`: Client libraries and programs for interacting with the server.
* `/tools`: Tools for development: setup, formatting, etc.
* `/LICENSE`: The license for this repository.
* `/CONTRIBUTING.md`: Information for those who contribute to the repo.

Table of Contents:

* [Getting Started](#getting-started)
  + [Prerequisites](#prerequisites)
  + [Computers and Networking](#computers-and-networking)
  + [Docker Images](#docker-images)
  + [Mission Configuration](#mission-configuration)
  + [Interop Integration](#interop-integration)
  + [Performance Evaluation](#performance-evaluation)
* [API Specification](#api-specification)
  + [Hostname & Port](#hostname--port)
  + [Relative URLs vs Full Resource URL](#relative-urls-vs-full-resource-url)
  + [Status Codes](#status-codes)
  + [Endpoints](#endpoints)
* [Automation](#automation)
  + [Configure Django](#configure-django)
  + [Import SUAS Code](#import-suas-code)
  + [Read & Write Objects](#read--write-objects)

## Getting Started

This section describes how to go from setting up the Interoperability Server to
completing interop tasks with the provided client library. The following code
and command examples work with the competition's host operating system, Ubuntu.

### Prerequisites

The Interoperability System builds on top a set of standard technologies. These
technologies should be learned and understood prior to using the
Interoperability System. The following are resources the reader can use to
learn these technologies.

* [Ubuntu](http://www.ubuntu.com/download/desktop/install-ubuntu-desktop)
* [Ubuntu Terminal](https://help.ubuntu.com/community/UsingTheTerminal)
* [Linux Shell](http://linuxcommand.org/learning_the_shell.php)
* [Git](https://git-scm.com/doc)
* [Github](https://guides.github.com/activities/hello-world)
* [Docker](https://docs.docker.com/engine/getstarted)
* [Python](https://docs.python.org/2/tutorial)
* [Virtualenv](https://virtualenv.pypa.io/en/stable)
* [Pip](https://pip.pypa.io/en/stable/user_guide)
* [Django](https://docs.djangoproject.com/en/1.8/intro)
* [Protobuf](https://developers.google.com/protocol-buffers/docs/pythontutorial)
* [Postgres](https://www.postgresql.org/docs/9.3/static/index.html)
* [Nginx](https://www.nginx.com)


### Computers and Networking

This subsection describes the computer and networking setup at competition. The
teams should replicate this setup to test their integration.

#### IP Addresses, Username, & Password

At Check-In and Orientation, teams will be given a static IP address, a DHCP IP
address range, the server IP address and port, a username, and a password. The
static IP address (e.g.  `10.10.130.100`) will be a single address unique to
the team which can be used to connect to the system. The DHCP range will be a
common range that will be provisioned to teams automatically by the interop
router. The router will be on the subnet `10.10.130.XXX` with subnet mask
`255.255.255.0`. The server IP address and port will be used to communicate
with the interop server (e.g.  `http://10.10.130.2:8000`). The username (e.g.
`testuser`) and password (e.g. `testpass`) will be the interop server login
credentials required to execute requests. The username will not be for a
superuser/administrator account on the server.

#### Interop Hardware

The hardware consists of a router and a computer. The router will be configured
to have a static IP address range, and a DHCP IP address range. All connected
judge computers will be at a static IP address.  The judges may also use
network configuration, like VLANs, to further isolate network traffic.

The judges have additional hardware to improve reliability of the interop
deployment. The judges use an additional computer to act as a black-box prober
which continuously executes requests to validate availability. The judges also
use UPS battery backups to prevent unavailability due to generator power loss.

During Mission Setup, the teams will be provided a single ethernet cord. This
cord will connect the team's system to the interop router, which will be
connected to the interop server. The mission clock will end once the team has
evacuated the runway and returned this ethernet cord.

#### Team Hardware

The judges recommend that teams use a router to have a separate subnet. The
judge provided ethernet cord will then connect a LAN port on the interop router
to the WAN port on the team's router. This will allow multiple team computers
to communicate with the interop server at the same time. This will also allow a
single computer to simultaneously communicate with the interop server and other
team computers.

The teams will need at least one computer to communicate with the interop
server. The judges recommend that teams leverage the provided client library
and tools, which are available in the client Docker image.  Teams may also
integrate directly via the HTTP + JSON protocol.

### Setup the Host Computer

Install `docker` with the [Docker Engine
Installation](https://docs.docker.com/engine/installation) guide.

Install `docker-compose` with the [Docker Compose
Installation](https://docs.docker.com/compose/install/) guide.

Install `git` with the [Git
Installation](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
guide.

From the command line you should have access to `docker`, `docker-compose`, and
`git`. Commands and scripts below will depend on these tools.

### Interop Git Repo

The interop server is developed using Git. Clone the repo to download scripts.

```bash
git clone https://github.com/auvsi-suas/interop.git
```

Now change directories into the interop folder. The following commands assume
they are run from the interop folder.

```bash
cd interop
```

### Docker Images

The Interoperability System is released to teams as Docker images and Docker
Compose YAML configurations. These can be used to run the server and client
tools with minimal setup.

#### auvsisuas/interop-server

##### First Time Setup

Change into the server subdirectory of the Git repo.

```bash
cd interop/server
```

Create the interop server's database.

```bash
sudo ./interop-server.sh create_db
```

Load initial test data into the server. This provides access to a default admin
account (u: `testadmin`, p: `testpass`) and a default team account (u:
`testuser`, p: `testpass`). This will also load a sample mission into the server.

```bash
sudo ./interop-server.sh load_test_data
```

##### Run the Server

Run the server on port 8000, so it can be accessed in a local web browser at
`localhost:8000`. Other machines on the same network can replace `localhost`
with the host computer's IP address.

```bash
sudo ./interop-server.sh up
```

The server will run until stopped using `Ctrl-C`.

##### View Server Log

Logs are also available via volumes on the host computer under
`volumes/var/log/uwsgi/interop.log`.

##### Upgrade the Server

Upgrade the Server by downloading new images, deleting the old containers, and
starting the server again.

```bash
sudo ./interop-server.sh upgrade
```

Note server data is persisted due to volumes. If the existing data causes an
issue, you can delete it (see next section).

##### Delete Server Data

While the server isn't running, you can delete the server data by deleting the
volumes and containers. Note this action is permanent.

```bash
sudo ./interop-server.sh rm_data
```

After deleting the data, you will need to follow First Time Setup instructions.

#### auvsisuas/interop-client

##### Create Container & Start Shell

Change into the client subdirectory of the Git repo.

```bash
cd interop/client
```

The interop client library and tools are provided as a Docker image and can be
run as a Docker container. The repo provides a script to run the container in a
standard way: it creates the container and starts a pre-configured shell.

```bash
sudo ./interop-client.sh run
```

##### Get Teams

The client image provides a script to request the status of teams from the
interoperability server, and it can be executed from the container shell. The
following shows how to execute it for the default testing user (`testuser`) if
the interop server was at `10.10.130.2:8000`.

```bash
./tools/interop_cli.py \
    --url http://10.10.130.2:8000 \
    --username testuser \
    teams
```

##### Get Mission

The client image provides a script to request mission details from the
interoperability server, and it can be executed from the container shell. The
following shows how to execute it for the default testing user (`testuser`) if
the interop server was at `10.10.130.2:8000`, requesting for mission ID 1.

```bash
./tools/interop_cli.py \
    --url http://10.10.130.2:8000 \
    --username testuser \
    mission \
    --mission_id 1
```

##### Upload Objects

The client image provides a script to upload detected objects to the interop
server from a directory of objects and thumbnails in the "Object File Format",
described in the appendix of the rules. The following shows how to upload
objects from the client container shell.

```bash
./tools/interop_cli.py \
    --url http://10.10.130.2:8000 \
    --username testuser \
    odlcs \
    --odlc_dir /path/to/object/directory
```

#### Continuous Integration

By default, Docker will use the `latest` tag which corresponds to the most
recently uploaded image. Using the `latest` tag will ensure you have the most
up-to-date code. For continuous integration (CI), however, this will cause
flakiness in CI reporting as your tests are unlikely to handle API or
implementation changes without manually adaptating your system. For CI, you'd
prefer to upgrade the container image version manually, adapting the system at
the same time (e.g. same commit).

The competition Docker images are tagged with the release month so teams can
manually specify versions for CI. These tags should be available for at least 3
months, allowing teams to use last month's frozen version for CI and to have a
month to upgrade between versions. Tags may be deleted after 3 months to
ensure teams upgrade. Closer to competition, tags younger than 3 months may be
deleted to ensure all changes are applied before competition.

To use a specific version, append the version to the named Docker image:

```bash
sudo docker pull auvsisuas/interop-server:2018.10
sudo docker pull auvsisuas/interop-client:2018.10
```

You can find the available tags here:
* https://hub.docker.com/r/auvsisuas/interop-server/tags
* https://hub.docker.com/r/auvsisuas/interop-client/tags

### Mission Configuration

This section describes how to configure a mission as an administrator on a
running interop server.

#### Preconfigured Users

The interop server Docker image comes with 2 users preconfigured: a test team
user (`testuser`, `testpass`), and a test admin user (`testadmin`, `testpass`).
At competition, the judges will have a secret admin account (`testadmin` will
be deleted), and the teams will be given a new team account (not `testuser`
with `testpass`). Don't confuse the capabilities of the two accounts! At
competition you will not have access to an admin account, so you will not be
able to see the following admin dashboards. Don't hard-code the username and
password!

#### Admin Web Login

The interop server has an admin webpage that can be used to configure the
server. Navigate to [http://localhost:8000](http://localhost:8000) in a web
browser. You may need to replace `localhost:8000` if you've configured the
setup differently. This will prompt for an admin account login, so enter the
preconfigured user: `testadmin` with password `testpass`.

#### SUAS Admin Dashboard

After login it will show the SUAS made admin dashboard. It will have a
navigation bar with system-wide and mission-specific links. The homepage for
the dashboard will also list the current missions, and should show the single
mission which comes with the image. If you click the mission, you will be
brought to a mission-specific dashboard.

* System

   * *Live View (KML)*. Downloads a KML file which can be opened in Google
     Earth to view real-time information. This provides a visualization that
     complements the one provided in this interface.
   * *Export Data (KML)*. Downloads a KML file which can be opened in Google
     Earth to view the UAS telemetry and other mission data after the mission
     is completed.
   * *Edit Data*. Opens the Django Admin Interface which can be used to
     configure missions and view raw data.
   * *Clear Cache*. Caching is used to improve performance of certain
     operations. The caches automatically expire, so users shouldn't need to
     use this, but data modification mid-mission may require explicit clearing
     to react faster.

* Mission

   * *Dashboard*. Navigates to the dashboard showing all mission elements,
     active team details, etc.
   * *Review Objects*. Navigates to the page to review objects submitted.
   * *Evaluate Teams*. Navigates to the page to download team evaluations.


#### Django Admin Dashboard

From the SUAS Admin Dashboard, you can use the menu `System > Edit Data` to
open the Django Admin dashboard. You should know how to use this interface from
the Prerequisite work.

#### Mission Configuration

To configure a mission, create or edit the `MissionConfig` object to specify
the desired flight boundaries, waypoints, true objects (for grading base
objects), etc.

#### Takeoff or Landing Events

When a team takes off and when a team lands, the interop judge creates a
`TakeoffOrLandingEvent` to mark the event. This is used to evaluate UAS
telemetry rates, waypoints, and collisions only while airborne.

### Interop Integration

This section provides examples for how to integrate with the interop server.
You are allowed to create custom integrations, so long as they follow the API.

#### Interop Client Docker Image

The competition provides a Docker image containing all of the client
integration tools. You can use these tools directly to integrate, or use the
Docker image as a base image for your own Docker images.

#### Interop Client Library

The competition provides a client library to make integration easier. It is
recommended that teams use this library to create a high-quality integration.
You can install the client library by executing setup commands listed
[here](https://github.com/auvsi-suas/interop/blob/master/client/Dockerfile).

To create a client object, import the `interop` module and construct the object
with the server URL, your username, and your password. The competition provides
two client objects: one which does synchronous requests, and another which does
asynchronous requests. The following examples show how to use the synchronous
form.

```python
from auvsi_suas.client import client
from auvsi_suas.proto import interop_api_pb2

client = client.Client(url='http://127.0.0.1:8000',
                       username='testuser',
                       password='testpass')
```

The following shows how to request the status of teams.

```python
teams = client.get_teams()
print(teams)
```

The following shows how to request the mission details.

```python
mission = client.get_mission(1)
print(mission)
```

The following shows how to upload UAS telemetry.

```python
telemetry= interop_api_pb2.Telemetry()
telemetry.latitude = 38
telemetry.longitude = -76
telemetry.altitude = 100
telemetry.heading = 90

client.post_telemetry(telemetry)
```

The following shows how to upload a object and it's image.

```python
odlc = interop_api_pb2.Odlc()
odlc.type = interop_api_pb2.Odlc.STANDARD
odlc.latitude = 38
odlc.longitude = -76
odlc.orientation = interop_api_pb2.Odlc.N
odlc.shape = interop_api_pb2.Odlc.SQUARE
odlc.shape_color = interop_api_pb2.Odlc.GREEN
odlc.alphanumeric = 'A'
odlc.alphanumeric_color = interop_api_pb2.Odlc.WHITE

odlc = client.post_odlc(odlc)

with open('path/to/image/A.jpg', 'rb') as f:
    image_data = f.read()
    client.put_odlc_image(odlc.id, image_data)
```

For more details on the API, see the code
[here](https://github.com/auvsi-suas/interop/tree/master/client/auvsi_suas/client).

#### MAVLink (ArduPilot) Integration

The Interop Client Image comes with MAVLink integration. Teams can use the
`interop_cli.py` command line tool to forward MAVLink messages to the
interoperability server.

##### MavProxy

The competition recommends using
[MavProxy](https://github.com/ArduPilot/MAVProxy>) to tee traffic, so that
telemetry goes to the Ground Control Station (e.g. [Mission
Planner](http://ardupilot.org/planner/docs/mission-planner-overview.html)) and
also to the `interop_cli.py` tool. See the [Getting
Started](http://ardupilot.github.io/MAVProxy/html/getting_started/download_and_installation.html)
guide for how to install and use the proxy. The specific command to use depends
on the setup. An example invocation to proxy one input stream to two output
streams:

```bash
mavproxy.py --out=127.0.0.1:14550 --out=127.0.0.1:14551
```

##### Interop Forwarding

You can use the `inteorp_cli.py` to read a MAVLink input stream, convert to
telemetry messages, and forward to the interoperability server. From the
Interop Client Docker Image:

```bash
./tools/interop_cli.py \
    --url http://10.10.130.2:8000 \
    --username testuser \
    mavlink \
    --device 127.0.0.1:14550
```

##### Ground Control Station

You can use a GCS like Mission Planner to control the MAVLink-based autopilot.
Configure the program to read the other `MavProxy` output port (in the example,
`14551`).


### Performance Evaluation

Once you have integrated with the Interoperability System, you should then
validate the integration by performing an end-to-end test. This should include
using the automatic evaluation the judges will use, which is provided as part
of the interop server.

Note that proper evaluation requires a representative `MissionConfig`, which
will include things like the flight boundaries and the details for the true
object detections.

#### Provide Human Judge Data

The first step is to provide the manual judge data. Go to `System > Edit Data`.
Select `Mission judge feedbacks >> add`.  Fill out the object with the mission,
user, and details about the team's performance, and then save.

#### Review Object Imagery

The second step is to review any object imagery provided. This is used to
review whether the provided image is acceptable, and whether human graded
features are correct (e.g. emergent object description).  It is not used to
grade whether the object details are correct (done automatically). Go to the
Mission Dashboard, and then use the menu `Mission > Review Objects`. Click on a
object ID to see the image and details, and then approve or reject the image,
and if applicable the emergent description.

#### Automatic Evaluation

The third step is to run the automatic evaluator.  Use the menu `Mission >
Evaluate Teams`. Select which users you want to evaluate, then hit `Evaluate`.
This will generate a zip file containing Json formatted feedback, and a CSV
file containing all team's data. Note that this operation filters superuser
accounts- testing must be done with a nonsuperuser (team) account. This output
contains the
[MissionEvaluation](https://github.com/auvsi-suas/interop/blob/master/server/auvsi_suas/proto/mission.proto)
and
[MultiOdlcEvaluation](https://github.com/auvsi-suas/interop/blob/master/server/auvsi_suas/proto/odlc.proto)
data.

## API Specification

This section describes the interoperability interface that is implemented by
the AUVSI SUAS competition server. Teams should use this documentation to
integrate with the competition server.

### Hostname & Port

The competition will specify the hostname and port of the server at the
competition. The hostname will be the IP address of the computer on which the
server is running, and the port will be the port selected when starting the
server. Teams must be able to specify this to their system during the mission.
The hostname can also be the hostname given to the computer. The hostname
"localhost" is a reserved name for the local host, and it resolves to the
loopback IP address `127.0.0.1`. An example hostname and port combination is
`192.168.1.2:8080`.

For testing, teams can setup the interop server on a computer they own and use
the computer's hostname and port to form an address.

### Relative URLs vs Full Resource URL

The relative URLs (endpoints) are described further in the following sections.
The interface defined in this document is what will be used at the competition.
Only slight changes may be made leading up to the competition to fix bugs or
add features. Teams should synchronize their code and check this documentation
for updates. An example relative URL is `/api/server_info`.

The full resource URL is the combination of the hostname, port, and relative
URL. This is the URL that must be used to make requests. An example full
resource URL is "http://192.168.1.2:80/api/login".

### Status Codes

Some of the HTTP status codes you may receive when using this API:

* `200`: The request was successful.

* `400`: The request was bad/invalid, the server does not know how to respond
  to such a request. Check the contents of the request.

* `401`: The request is unauthorized. Check that you've logged into the server
  and are passing the credentials cookie on each request.

* `403`: The request is forbidden. Check that you are not accessing an
  administrative API as a non-administrative user. At competition, teams will
  not have access to administrative APIs.

* `404`: The request was made to an invalid URL, the server does not know how
  to respond to such a request. Check the endpoint URL.

* `405`: The request used an invalid method (e.g., `GET` when only `POST` is
  supported). Double check the documentation below for the methods supported by
  each endpoint.

* `500`: The server encountered an internal error and was unable to process the
  request. This indicates a configuration error on the server side.

### Endpoints

Below are all of the endpoints provided by the server, displayed by their
relative URL, and the HTTP method with which you access them.

Some endpoints take JSON requests or return JSON responses. The format of the
JSON data is defined in the
[Interop API Proto](https://github.com/auvsi-suas/interop/blob/master/proto/interop_api.proto).

#### User Login

##### POST /api/login

Teams must login to the competition server by making an HTTP POST request with
a `LoginRequest` JSON formatted proto. Teams only need to make a login once
before any other requests. The login request, if successful, will return
cookies that uniquely identify the user and the current session. Teams must
send these cookies to the competition server in all future requests.

Example Request:

```http
POST /api/login HTTP/1.1
Host: 192.168.1.2:8000
Content-Type: application/json

{
    "username": "testadmin",
    "password": "testpass"
}
```

Example Response:

```http
HTTP/1.1 200 OK
Set-Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi; expires=Mon, 17-Aug-2015 02:41:09 GMT; httponly; Max-Age=1209600; Path=/

Login Successful.
```

#### Teams

##### GET /api/teams

This endpoint gets the status of teams. Returns a list of `TeamStatus` JSON
formatted proto.

Example Request:

```http
GET /api/teams HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json
[{
  "team": {
    "id": 2,
    "username": "testuser",
    "name": "Team Name",
    "university": "Team University"
  },
  "inAir": false,
  "telemetry": {
    "latitude": 0.0,
    "longitude": 0.0,
    "altitude": 0.0,
    "heading": 0.0
  },
  "telemetryId": "1278",
  "telemetryAgeSec": 1.064382,
  "telemetryTimestamp": "2019-10-05T20:42:23.643989+00:00"
}]
```

#### Missions

##### GET /api/missions/(int:id)

This endpoint gets the details about a mission with id `id`, and returns a
`Mission` JSON formatted proto.

Example Request:

```http
GET /api/missions/1 HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "lostCommsPos": {
    "latitude": 38.145103,
    "longitude": 38.145103
  },
  "offAxisOdlcPos": {
    "latitude": 38.145111,
    "longitude": -76.427861
  },
  "stationaryObstacles": [
    {
      "latitude": 38.146689,
      "radius": 150.0,
      "longitude": -76.426475,
      "height": 750.0
    },
    {
      "latitude": 38.142914,
      "radius": 300.0,
      "longitude": -76.430297,
      "height": 300.0
    },
    {
      "latitude": 38.149504,
      "radius": 100.0,
      "longitude": -76.43311,
      "height": 750.0
    },
    {
      "latitude": 38.148711,
      "radius": 300.0,
      "longitude": -76.429061,
      "height": 750.0
    },
    {
      "latitude": 38.144203,
      "radius": 50.0,
      "longitude": -76.426155,
      "height": 400.0
    },
    {
      "latitude": 38.146003,
      "radius": 225.0,
      "longitude": -76.430733,
      "height": 500.0
    }
  ],
  "searchGridPoints": [
    {
      "latitude": 38.1444444444444,
      "longitude": -76.4280916666667
    },
    {
      "latitude": 38.1459444444444,
      "longitude": -76.4237944444445
    },
    {
      "latitude": 38.1439305555556,
      "longitude": -76.4227444444444
    },
    {
      "latitude": 38.1417138888889,
      "longitude": -76.4253805555556
    },
    {
      "latitude": 38.1412111111111,
      "longitude": -76.4322361111111
    },
    {
      "latitude": 38.1431055555556,
      "longitude": -76.4335972222222
    },
    {
      "latitude": 38.1441805555556,
      "longitude": -76.4320111111111
    },
    {
      "latitude": 38.1452611111111,
      "longitude": -76.4289194444444
    },
    {
      "latitude": 38.1444444444444,
      "longitude": -76.4280916666667
    }
  ],
  "waypoints": [
    {
      "latitude": 38.1446916666667,
      "altitude": 200.0,
      "longitude": -76.4279944444445
    },
    {
      "latitude": 38.1461944444444,
      "altitude": 300.0,
      "longitude": -76.4237138888889
    },
    {
      "latitude": 38.1438972222222,
      "altitude": 400.0,
      "longitude": -76.42255
    },
    {
      "latitude": 38.1417722222222,
      "altitude": 400.0,
      "longitude": -76.4251083333333
    },
    {
      "latitude": 38.14535,
      "altitude": 300.0,
      "longitude": -76.428675
    },
    {
      "latitude": 38.1508972222222,
      "altitude": 300.0,
      "longitude": -76.4292972222222
    },
    {
      "latitude": 38.1514944444444,
      "altitude": 300.0,
      "longitude": -76.4313833333333
    },
    {
      "latitude": 38.1505333333333,
      "altitude": 300.0,
      "longitude": -76.434175
    },
    {
      "latitude": 38.1479472222222,
      "altitude": 200.0,
      "longitude": -76.4316055555556
    },
    {
      "latitude": 38.1443333333333,
      "altitude": 200.0,
      "longitude": -76.4322888888889
    },
    {
      "latitude": 38.1433166666667,
      "altitude": 300.0,
      "longitude": -76.4337111111111
    },
    {
      "latitude": 38.1410944444444,
      "altitude": 400.0,
      "longitude": -76.4321555555556
    },
    {
      "latitude": 38.1415777777778,
      "altitude": 400.0,
      "longitude": -76.4252472222222
    },
    {
      "latitude": 38.1446083333333,
      "altitude": 200.0,
      "longitude": -76.4282527777778
    }
  ],
  "airDropPos": {
    "latitude": 38.1458416666667,
    "longitude": -76.426375
  },
  "emergentLastKnownPos": {
    "latitude": 38.145111,
    "longitude": -76.427861
  },
  "ugvDrivePos": {
    "latitude": 38.145103,
    "longitude": -76.427856
  },
  "flyZones": [
    {
      "altitudeMax": 750.0,
      "altitudeMin": 100.0,
      "boundaryPoints": [
        {
          "latitude": 38.1462694444444,
          "longitude": -76.4281638888889
        },
        {
          "latitude": 38.151625,
          "longitude": -76.4286833333333
        },
        {
          "latitude": 38.1518888888889,
          "longitude": -76.4314666666667
        },
        {
          "latitude": 38.1505944444444,
          "longitude": -76.4353611111111
        },
        {
          "latitude": 38.1475666666667,
          "longitude": -76.4323416666667
        },
        {
          "latitude": 38.1446666666667,
          "longitude": -76.4329472222222
        },
        {
          "latitude": 38.1432555555556,
          "longitude": -76.4347666666667
        },
        {
          "latitude": 38.1404638888889,
          "longitude": -76.4326361111111
        },
        {
          "latitude": 38.1407194444444,
          "longitude": -76.4260138888889
        },
        {
          "latitude": 38.1437611111111,
          "longitude": -76.4212055555556
        },
        {
          "latitude": 38.1473472222222,
          "longitude": -76.4232111111111
        },
        {
          "latitude": 38.1461305555556,
          "longitude": -76.4266527777778
        }
      ]
    }
  ],
  "id": 1
}

```

#### UAS Telemetry

##### POST /api/telemetry

Teams make requests to upload the UAS telemetry to the competition server.
Takes a `Telemetry` JSON formatted proto.

Each telemetry request should contain unique telemetry data. Duplicated data
will be accepted but not evaluated.

Example Request:

```http
POST /api/telemetry HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
Content-Type: application/json

{
  "latitude": 38,
  "longitude": -75,
  "altitude": 50,
  "heading": 90
}
```

#### Object Detection, Localization, Classification (ODLC)

##### POST /api/odlcs

This endpoint is used to upload a new odlc for submission. All odlcs uploaded
at the end of the mission time will be evaluated by the judges. Takes a `Odlc`
JSON formatted proto and returns the durable ODLC with assigned ID.

Most of the odlc characteristics are optional; if not provided in this
initial POST request, they may be added in a future PUT request.
Characteristics not provided will be considered left blank. Note that some
characteristics must be submitted by the end of the mission to earn credit
for the odlc.

Example Request:

```http
POST /api/odlcs HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
Content-Type: application/json

{
  "mission": 1,
  "type": "STANDARD",
  "latitude": 38,
  "longitude": -76,
  "orientation": "N",
  "shape": "RECTANGLE",
  "shapeColor": "RED",
  "autonomous": false
}
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "mission": 1,
  "type": "STANDARD",
  "latitude": 38,
  "longitude": -76,
  "orientation": "N",
  "shape": "RECTANGLE",
  "shapeColor": "RED",
  "autonomous": false
}
```

##### PUT /api/odlcs/(int:id)

Update odlc id `id`. This endpoint allows you to specify characteristics that
were omitted in `POST /api/odlcs`, or update those that were specified. Takes
an `Odlc` JSON formatted proto and returns the updated ODLC in the same format.

Example Request:

```http
PUT /api/odlcs/1 HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
Content-Type: application/json

{
  "id": 1,
  "mission": 1,
  "type": "STANDARD",
  "latitude": 38,
  "longitude": -76,
  "orientation": "N",
  "shape": "CIRCLE",
  "shapeColor": "RED",
  "autonomous": false
}
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "mission": 1,
  "type": "STANDARD",
  "latitude": 38,
  "longitude": -76,
  "orientation": "N",
  "shape": "CIRCLE",
  "shapeColor": "RED",
  "autonomous": false
}
```

##### GET /api/odlcs

This endpoint is used to retrieve a list of odlcs uploaded. Returns a list of
`Odlc` JSON formatted proto.

This endpoint will only return up to 100 odlcs. It is recommended to remain
below 100 odlcs total (there certainly won't be that many at competition!). If
you do have more than 100 odlcs, individual odlcs may be queried with `GET
/api/odlcs/(int:id)`.

Example Request:

```http
GET /api/odlcs HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": 1,
    "mission": 1,
    "type": "STANDARD",
    "latitude": 38,
    "longitude": -76,
    "orientation": "N",
    "shape": "RECTANGLE",
    "shapeColor": "RED",
    "autonomous": false
  },
  {
    "id": 1,
    "mission": 2,
    "type": "OFF_AXIS",
    "latitude": 39,
    "longitude": -75,
    "orientation": "S",
    "shape": "CIRCLE",
    "shapeColor": "BLUE",
    "autonomous": true
  }
]
```

The endpoint also takes an optional GET parameter to restrict the returned
ODLCs to the ones for a specific mission.

Example Request:

```http
GET /api/odlcs?mission=1 HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

##### GET /api/odlcs/(int:id)

Details about a odlc id `id`. This simple endpoint allows you to verify the
uploaded characteristics of a odlc. Returns an `Odlc` JSON formatted proto.

Example Request:

```http
GET /api/odlcs/1 HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

Note: This example reformatted for readability; actual response may be
entirely on one line.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "mission": 1,
  "type": "STANDARD",
  "latitude": 38,
  "longitude": -76,
  "orientation": "N",
  "shape": "RECTANGLE",
  "shapeColor": "RED",
  "autonomous": false
}
```

##### POST /api/odlcs/(int:id)/image

Add or update odlc image thumbnail.

`id` is the unique identifier of a odlc, as returned by
`POST /api/odlcs`. See `GET /api/odlcs/(int:id)` for more
information about the odlc ID.

This endpoint is used to submit an image of the associated odlc. This
image should be a clear, close crop of the odlc. Subsequent calls to this
endpoint replace the odlc image.

The request body contains the raw binary content of the image. The image
should be in either JPEG or PNG format. The request must not exceed 1 MB in
size.

Example Request:

```http
POST /api/odlcs/2/image HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
Content-Type: image/jpeg

<binary image content ...>
```http

Example Response:

```http
HTTP/1.1 200 OK

Image uploaded.
```

##### PUT /api/odlcs/(int:id)/image

Equivalent to `POST /api/odlcs/(int:id)/image`.

##### GET /api/odlcs/(int:id)/image

Download previously uploaded odlc thumbnail. This simple endpoint returns
the odlc thumbnail uploaded with a
`POST /api/odlcs/(int:id)/image` request.

`id` is the unique identifier of a odlc, as returned by
`POST /api/odlcs`. See `GET /api/odlcs/(int:id)` for more
information about the odlc ID.

The response content is the image content itself on success.

Example Request:

```http
GET /api/odlcs/2/image HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

```http
HTTP/1.1 200 OK
Content-Type: image/jpeg

<binary image content ...>
```

##### DELETE /api/odlcs/(int:id)/image

Delete odlc image thumbnail.

`id` is the unique identifier of a odlc, as returned by
`POST /api/odlcs`.

This endpoint is used to delete the image associated with a odlc. A deleted
image will not be used in scoring.

NOTE: You do not need to delete the odlc image before uploading a new image.  A
call to `POST /api/odlcs/(int:id)/image` or `PUT /api/odlcs/(int:id)/image`
will overwrite the existing image.

Example Request:

```http
DELETE /api/odlcs/2/image HTTP/1.1
Host: 192.168.1.2:8000
Cookie: sessionid=9vepda5aorfdilwhox56zhwp8aodkxwi
```

Example Response:

```http
HTTP/1.1 200 OK

Image deleted.
```

## Automation

This section describes how to write admin automation for the interop server by
writing scripts which connect directly to the database and bypass the
webserver. Note that the database and Django configurations only permit local
access, so you'll need to run any such scripts locally. This may be useful
while testing to automatically setup test cases (e.g. test mission) or analyze
results (e.g. turning radius).

### Configure Django

The first step when writing a script is to import Django and have it setup for
programmatic access. Start the script with the following:

```python
import os
import sys

# Add server code to Python PATH for imports.
sys.path.append('/path/to/server')
# Add environment variable to get Django settings file.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

# Setup Django.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Import SUAS Code

The next step is to import the various models that you want to access. The
following shows how to import the ``MissionConfig`` and ``GpsPosition`` models.

```python
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig
```

### Read & Write Objects

The following shows how to read all ``MissionConfig`` objects and save a
``GpsPosition`` object. For details on how to perform actions like this on
Django models, see the [Django
Tutorials](https://docs.djangoproject.com/en/1.10/intro/).

```python
# Print all mission objects.
print(MissionConfig.objects.all())

# Create and save a GPS position.
gpos = GpsPosition(latitudel=38.145335, longitude=-76.427512)
gpos.save()
```
