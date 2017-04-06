Getting Started
===============

This section describes how to go from setting up the Interoperability Server to
completing interop tasks with the provided client library. The following code
and command examples work with the competition's host operating system, Ubuntu
16.04.


Prerequisites
-------------

The Interoperability System builds on top a set of standard technologies. These
technologies should be learned and understood prior to using the
Interoperability System. The following are resources the reader can use to
learn these technologies.

#. `Ubuntu 16.04 <http://www.ubuntu.com/download/desktop/install-ubuntu-desktop>`__
#. `Ubuntu Terminal <https://help.ubuntu.com/community/UsingTheTerminal>`__
#. `Linux Shell <http://linuxcommand.org/learning_the_shell.php>`__
#. `Git <https://git-scm.com/doc>`__
#. `Github <https://guides.github.com/activities/hello-world/>`__
#. `Docker <https://docs.docker.com/engine/getstarted/>`__
#. `Python <https://docs.python.org/2/tutorial/>`__
#. `Virtualenv <https://virtualenv.pypa.io/en/stable/>`__
#. `Pip <https://pip.pypa.io/en/stable/user_guide/>`__
#. `Django <https://docs.djangoproject.com/en/1.8/intro/>`__
#. `Postgres <https://www.postgresql.org/docs/9.3/static/index.html>`__
#. `Apache <http://httpd.apache.org/docs/2.0/>`__


Computers and Networking
------------------------

This subsection describes the computer and networking setup at competition. The
teams should replicate this setup to test their integration.

**IP Addresses, Username, & Password.** At Check-In and Orientation, teams will
be given a static IP address, a DHCP IP address range, the server IP address
and port, a username, and a password. The static IP address (e.g.
``10.10.130.100``) will be a single address unique to the team which can be used
to connect to the system. The DHCP range will be a common range that will be
provisioned to teams automatically by the interop router. The router will be on
the subnet ``10.10.130.XXX`` with subnet mask ``255.255.255.0``. The server IP
address and port will be used to communicate with the interop server (e.g.
``http://10.10.130.2:8000``). The username (e.g. ``testuser``) and password
(e.g. ``testpass``) will be the interop server login credentials required to
execute requests. The username will not be for a superuser/administrator
account on the server.

**Ethernet Cord.** During Mission Setup, the teams will be provided a single
ethernet cord. This cord will connect the team's system to the interop router,
which will be connected to the interop server. The mission clock will end once
the team has evacuated the runway and returned this ethernet cord.

The following shows how the Interoperability System will be connected, and the
recommended means of connecting the team's system. Note the IP addresses are
examples.

.. graphviz::

  graph interop {
    splines=ortho;
    node [shape=box];
    subgraph cluster_judges {
      color=blue;
      label="Judges";
      subgraph cluster_interop_router {
        style=filled;
        color=lightgrey;
        label="Interop Router: 10.10.130.1";
        node [style=filled,color=white];
          interop_lan0 [label="LAN 0: 10.10.130.2"];
        interop_lan1 [label="LAN 1: 10.10.130.3"];
        interop_lan1 -- interop_lan0;
      }
      interop_server [label="Interop Server: 10.10.130.2"];
      interop_lan0 -- interop_server;
   }

    subgraph cluster_team {
      color=blue;
      label="Team";
      subgraph cluster_team_router {
        style=filled;
        color=lightgrey;
        label="Team Router: 192.168.1.1";
        node [style=filled,color=white];
        team_wlan [label="WLAN: 10.10.130.3"];
        team_lan0 [label="LAN 0: 192.168.1.2"];
        team_wlan -- team_lan0;
      }
      team_computer [label="Team Computer: 192.168.1.2"];
      team_lan0 -- team_computer;
    }

    interop_lan1 -- team_wlan [constraint=false];
  }

**Interop Hardware**. The hardware consists of a router and a computer. The
router will be configured to have a static IP address range, and a DHCP IP
address range. All connected judge computers will be at a static IP address.
The judges may also use network configuration, like VLANs, to further isolate
network traffic. The interop host machine will be a computer running Ubuntu
14.04 or 16.04, and will run the server Docker image to host the inteorp server.

**Interop Supporting Hardware**. The judges have additional hardware to improve
reliability of the interop deployment. The judges use an additional computer to
act as a black-box prober which continuously executes requests to validate
availability. The judges also use UPS battery backups to prevent unavailability
due to generator power loss.

**Team Router**. The judges recommend that teams use a router to have a
separate subnet. The judge provided ethernet cord will then connect a LAN port
on the interop router to the WAN port on the team's router. This will allow
multiple team computers to communicate with the interop server at the same
time. This will also allow a single computer to simultaneously communicate with
the interop server and other team computers.

**Team Machine**. The teams will need at least one computer to communicate with
the interop server. The judges recommend that teams leverage the provided
client library and tools, which are available in the client Docker image.
Teams may also integrate directly via the HTTP + JSON protocol.


Git Repository
--------------

The Interoperability System is developed through the `AUVSI SUAS Competition
Repository <https://github.com/auvsi-suas/interop>`__. The first step is to
clone the repository locally.

.. code-block:: bash

    sudo apt-get install -y git
    cd ~/
    git clone https://github.com/auvsi-suas/interop.git


Docker Images
-------------

The Interoperability System is released to teams as Docker images.  The images
can be used to run the server and client tools with minimal setup.

**Setup the Host Computer**. The next step is to setup the host computer
(Ubuntu 16.04) to run Docker images. The repo provides a script in the
repository to do such.  For alternative deployments, you can use the `Docker
Engine Installation <https://docs.docker.com/engine/installation/>`__ guide.

.. code-block:: bash

    cd ~/interop
    sudo ./tools/setup_docker.sh


auvsisuas/interop-server
~~~~~~~~~~~~~~~~~~~~~~~~

**Create and Start Container**. The interop server is provided as a Docker
image and should be run as a Docker container. The repo provides a script to
run the container in a standard way: it creates the container, runs it in the
background, uses port ``8000`` for the web server, and restarts automatically
(e.g. on failure or boot) unless explicitly stopped.

.. code-block:: bash

    cd ~/interop
    sudo ./server/run.sh

**Stop and Start**. Once the server is running, it can be stopped and started
again. Note that the ``run.sh`` creates and starts the container- it can't be
used to start an existing stopped container. The following can start and stop
the container.

.. code-block:: bash

    sudo docker stop interop-server
    sudo docker start interop-server

**Container Shell**. To inspect state, use local server tools (e.g. Django's
management tool), or do other container-local actions, you can start a bash
shell inside of the container. The following shows how to start the shell.

.. code-block:: bash

    sudo docker exec -it interop-server bash

**Dump Database, Dump Server Log**. The shell will start the user inside of the
working directory (server source code) at ``/interop/server``. The following
shows how to dump the database to standard output, dump the server log file to
standard output, and exit the shell.

.. code-block:: bash

    cd /interop/server
    python manage.py dumpdata

    cd /var/log/apache2
    cat interop_server_error.log

    exit

**Remove Container**. The container will maintain database and log state
between starts and stops of the same container. The state, which includes data
like telemetry will automatically be deleted if the container is removed. The
following can remove a container.

.. code-block:: bash

    sudo docker stop interop-server
    sudo docker rm interop-server


auvsisuas/interop-client
~~~~~~~~~~~~~~~~~~~~~~~~

**Create Container & Start Shell**. The interop client library and tools are
provided as a Docker image and can be run as a Docker container. The repo
provides a script to run the container in a standard way: it creates the
container and starts a pre-configured shell.

.. code-block:: bash

    cd ~/interop
    sudo ./client/run.sh

**Get Missions**. The client image provides a script to request mission details
from the interoperability server, and it can be executed from the container
shell. The following shows how to execute it for the default testing user
(``testuser``) if the interop server was at ``10.10.130.2:8000``.

.. code-block:: bash

    ./tools/interop_cli.py --url http://10.10.130.2:8000 --username testuser missions

**Upload Targets**. The client image provides a script to upload targets to the
interop server from a directory of targets and target thumbnails in the "Object
File Format", described in the appendix of the 2017 rules. The following shows
how to upload targets from the client container shell.

.. code-block:: bash

    ./tools/interop_cli.py --url http://10.10.130.2:8000 --username testuser targets \
        --target_dir /path/to/target/directory/

**Probe Server**. The client image provides a script to continuously execute
dummy interop requests to test server availability. The following shows how to
execute the prober from the client container shell.

.. code-block:: bash

    ./tools/interop_cli.py --url http://10.10.130.2:8000 --username testuser probe


Mission Configuration
---------------------

This section describes how to configure a mission as an administrator on a
running interop server.

**Preconfigured Users**. The interop server Docker image comes with 2 users
preconfigured: a test team user (``testuser``, ``testpass``), and a test admin
user (``testadmin``, ``testpass``). At competition, the judges will have a
secret admin account (``testadmin`` will be deleted), and the teams will be
given a new team account (not ``testuser`` with ``testpass``). Don't confuse
the capabilities of the two accounts! At competition you will not have access
to an admin account, so you will not be able to see the following admin
dashboards. Don't hard-code the username and password!

**Admin Web Login**. The interop server has an admin webpage that can be used
to configure the server. Navigate to `<http://localhost:8000>`__ in a web
browser. You may need to replace ``localhost:8000`` if you've configured the
setup differently. This will prompt for an admin account login, so enter the
preconfigured user: ``testadmin`` with password ``testpass``.

**SUAS Admin Dashboard**. After login it will show the SUAS made admin
dashboard. It will have a navigation bar with system-wide and mission-specific
links. The homagepage for the dashboard will also list the current missions,
and should show the single mission which comes with the image. If you click the
mission, you will be brought to a mission-specific dashboard. Click the "Help"
button on the mission dashboard to learn how to use this interface.

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
   * *Review Targets*. Navigates to the page to review targets submitted.
   * *Evaluate Teams*. Navigates to the page to download team evaluations.


**Django Admin Dashboard**. From the SUAS Admin Dashboard, you can use the menu
``System > Edit Data`` to open the Django Admin dashboard. You should know how
to use this interface from the Prerequisite work. See :doc:`configuration` for
more details.

**Mission Configuration**. To configure a mission, create or edit the
``MissionConfig`` object to specify the desired flight boundaries, waypoints,
true targets (for grading base targets), etc. Once the updated mission and
subobjects have been saved, the cache should be cleared via the SUAS
Dashboard's menu ``System > Clear Cache``.

**Mission Clock Events**. When the mission clock for a team starts, the interop
judge creates a ``MissionClockEvent`` for the team indicating the team has gone
on the clock. The judge creates another object to indicate the team has gone
off the clock. The time is automatically set at time of save. This is used to
evaluate mission clock time and to ensure target review doesn't start before
targets are frozen.

**Takeoff or Landing Events**. When a team takes off and when a team lands, the
interop judge creates a ``TakeoffOrLandingEvent`` to mark the evenet. The time
is automatically set at time of save. This is used to evaluate UAS telemetry
rates, waypoints, and collisions only while airborne.


Interop Integration
-------------------

This section provides examples for how to integrate with the interop server
beyond using the provided tools.


Example Request with CURL
~~~~~~~~~~~~~~~~~~~~~~~~~

The following is an example of how to perform interoperability using the
``curl`` command. **This is too inefficient to achieve a sufficient
update rate**. This merely shows how simple it is to implement
interoperability from standard HTTP and JSON.

The curl command has the following parameters:

#. **--cookie**: Cookies in this file are sent to the server.
#. **--cookie-jar**: Cookies sent from the server are saved in this file.
#. **--data**: Makes the request a POST request instead of GET request,
   and sends the given argument as the POST data segment.
#. **[URL]**: The URL to make a request to. This consists of a hostname
   (localhost:8080) and a relative path (/api/interop/server\_info).

Try the following commands, and see the effect on the stored data at the
server:

.. code-block:: bash

    curl --cookie cookies.txt --cookie-jar cookies.txt \
       --data "username=testuser&password=testpass" \
       http://localhost:8080/api/login

    curl --cookie cookies.txt --cookie-jar cookies.txt \
       http://localhost:8080/api/missions

    curl --cookie cookies.txt --cookie-jar cookies.txt \
       http://localhost:8080/api/obstacles

    curl --cookie cookies.txt --cookie-jar cookies.txt \
       --data "latitude=10&longitude=20&altitude_msl=30&uas_heading=40" \
       http://localhost:8080/api/telemetry


Client Library
~~~~~~~~~~~~~~

The competition provides a :doc:`client` to make integration easier. It is
recommended that teams use this library to create a high-quality integration.

To create a client, import the ``interop`` module and construct the object with
the server URL, your username, and your password. The competition provides two
client objects: one which does synchronous requests, and another which does
asynchronous requests. The following examples show how to use the synchronous
form.

.. code:: python

    import interop

    client = interop.Client(url='http://127.0.0.1:8000',
                            username='testuser',
                            password='testpass')

The following shows how to request the mission details and the current position
of the obstacles.

.. code:: python

    missions = client.get_missions()
    print missions

    stationary_obstacles, moving_obstacles = client.get_obstacles()
    print stationary_obstacles, moving_obstacles


The following shows how to upload UAS telemetry.

.. code:: python

    telemetry = interop.Telemetry(latitude=38.145215,
                                  longitude=-76.427942,
                                  altitude_msl=50,
                                  uas_heading=90)
    client.post_telemetry(telemetry)

The following shows how to upload a target and it's image.

.. code:: python

    target = interop.Target(type='standard',
                            latitude=38.145215,
                            longitude=-76.427942,
                            orientation='n',
                            shape='square',
                            background_color='green',
                            alphanumeric='A',
                            alphanumeric_color='white')
    target = client.post_target(target)

    with open('path/to/image/A.jpg', 'rb') as f:
        image_data = f.read()
        client.put_target_image(target.id, image_data)


MAVLink (ArduPilot) Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Interop Client Image comes with MAVLink integration. Teams can use the
``interop_cli.py`` command line tool to forward MAVLink messages to the
interoperability server.

**MavProxy**. The competition recommends using `MavProxy
<https://github.com/ArduPilot/MAVProxy>`__ to tee traffic, so that telemetry
goes to the Ground Control Station (e.g. `Mission Planner
<http://ardupilot.org/planner/docs/mission-planner-overview.html>`__) and also
to the ``interop_cli.py`` tool. See the `Getting Started
<http://ardupilot.github.io/MAVProxy/html/getting_started/download_and_installation.html>`__
guide for how to install and use the proxy. The specific command to use depends
on the setup. An example invocation to proxy one input stream to two output
streams:

.. code-block:: bash

    mavproxy.py --out=127.0.0.1:14550 --out=127.0.0.1:14551

**Interop Forwarding**. You can use the ``inteorp_cli.py`` to read a MAVLink
input stream, convert to telemetry messages, and forward to the
interoperability server. From the Interop Client Image:

.. code-block:: bash

    ./tools/interop_cli.py --url http://10.10.130.2:8000 --username testuser \
        mavlink --device 127.0.0.1:14550

**Ground Control Station**. You can use a GCS like Mission Planner to control
the MAVLink-based autopilot. Configure the program to read the other
``MavProxy`` output port (in the example, ``14551``).


Performance Evaluation
----------------------

Once you have integrated with the Interoperability System, you should then
validate the integration by performing an end-to-end test. This should include
using the automatic evaluation the judges will use, which is provided as part
of the interop server.

Note that proper evaluation requires a representative ``MissionConfig``, which
will include things like the flight boundaries and the details for the true
targets.

**Review Target Imagery**. The first step is to review any target imagery
provided. This is used to review whether the provided image is acceptable, and
whether human graded features are correct (e.g. emergent target description).
It is not used to grade whether the target details are correct (done
automatically). Go to the Mission Dashboard, and then use the menu ``Mission >
Review Targets``. Click on a target ID to see the image and details, and then
approve or reject the image, and if applicable the emergent description.

**Automatic Evaluation**. The second step is to run the automatic evaluator.
Use the menu ``Mission > Evaluate Teams (CSV)``. This will generate a CSV file,
with one line for every team (non superuser account), and one column for every
gradable deliverable / performance feedback.
