System Testing
==============

The competition server comes with many tests to evaluate the system. You
should execute these tests after you have installed the system, or after
any code updates (git pull). If the tests do not pass then you will
likely have trouble testing your interoperability implementation.

To run the tests execute the following commands:

.. code-block:: bash

    $ cd ~/interop/server
    $ python manage.py test auvsi_suas

The tests have executed successfully if you see these lines::

    Ran [X] tests in [Y]s

    OK

These tests will do the following:

#. **Evaluate Code Correctness**. For each line of code it will run
   automated tests to ensure code correctness. This includes both model
   code like the code to determine distance between GPS points, and the
   view code like the code to login the user.
#. **Determine Max System Load**. The code will exercise the interfaces
   to ensure in isolation they can achieve the required interaction
   rates. This will validate both code efficiency, and the system setup.
   Each interaction must operate at 10 Hz while doing 3 operations
   simultaneously, so 30 Hz each in isolation. The rates achieved will
   be printed to the screen, and if the rates are below 30 Hz then the
   test will fail.

If the tests fail:

-  **Code Correctness**. The code is tested before it is uploaded to the
   repository. A failure due to code correctness will usually be due to
   a missing dependency or incorrect configuration. Use the test output
   to debug and fix the discrepancy.
-  **Load Tests**. The code is tested to interact at sufficient rates on
   sample hardware before it is uploaded to the repository. A failure
   usually means that the setup is insufficient resource-wise. This may
   mean you don't have a fast enough CPU, enough RAM, a fast enough
   disk, etc. Please consider using a dedicated machine (not
   virtualized) with modern hardware, and only run the competition
   server on this computer.

**Current Expected Performance**. At the time of writing this page, the
tests were executing at 100+ Hz on a virtualized OS on old hardware (5+
years), and at 400+ Hz on a dedicated computer with current hardware (<
1 year). These numbers are much larger than the required 30 Hz. It
should also be noted that deployment will be higher performing than
these tests. The deployed version will not be in debug mode, and will
use a high performance web server in addition to the Django application.
The judges have also confirmed with some teams that their
interoperability implementations have achieved the required 10 Hz.
