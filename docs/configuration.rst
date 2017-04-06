Configuration
=============

This section describes how to configure the interop server. Additional steps
for deployment can be found in `Django's Deployment Docs
<https://docs.djangoproject.com/en/1.8/howto/deployment/>`__.


**Create a New Admin**. The automated system setup will create a default
administrator account with username ``testadmin`` and password ``testpass``.
This account can be used to login to the admin interfaces or authenticate any
requests. If you would like to create another administrator account, the
Django management program can be used to create an administrator account.
Execute the following from a bash shell inside the server's container.

.. code-block:: bash

    cd /interop/server
    python manage.py createsuperuser



Object Configuration
--------------------

The following describes the individual model objects in greater
detail than what is presented in :doc:`getting_started`.

.. autoclass:: auvsi_suas.models.gps_position.GpsPosition
.. autoclass:: auvsi_suas.models.aerial_position.AerialPosition
.. autoclass:: auvsi_suas.models.uas_telemetry.UasTelemetry
.. autoclass:: auvsi_suas.models.target.Target
.. autoclass:: auvsi_suas.models.waypoint.Waypoint
.. autoclass:: auvsi_suas.models.stationary_obstacle.StationaryObstacle
.. autoclass:: auvsi_suas.models.moving_obstacle.MovingObstacle
.. autoclass:: auvsi_suas.models.fly_zone.FlyZone
.. autoclass:: auvsi_suas.models.mission_config.MissionConfig
.. autoclass:: auvsi_suas.models.mission_clock_event.MissionClockEvent
.. autoclass:: auvsi_suas.models.takeoff_or_landing_event.TakeoffOrLandingEvent
.. autoclass:: auvsi_suas.models.mission_judge_feedback.MissionJudgeFeedback

