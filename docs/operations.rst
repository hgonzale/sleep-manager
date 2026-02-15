Operations
==========

Service management
------------------

.. code-block:: bash

   sudo systemctl start sleep-manager
   sudo systemctl enable sleep-manager
   sudo systemctl stop sleep-manager
   sudo systemctl disable sleep-manager
   sudo systemctl status sleep-manager

Logs
----

.. code-block:: bash

   sudo journalctl -u sleep-manager -f
   sudo journalctl -u sleep-manager --since "1 hour ago"

API checks
----------

.. code-block:: bash

   # Health checks
   curl http://sleeper_url:51339/health
   curl http://waker_url:51339/health

   # Sleeper status (sleeper machine)
   curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status

   # Waker status — returns state machine state, does not proxy to sleeper
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
   # {"op": "status", "state": "ON", "homekit": "on"}

   # Wake the sleeper
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

   # Suspend the sleeper via the waker
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

State machine
-------------

The waker maintains a state machine with four states:

* ``OFF`` — sleeper is not running; no heartbeat received.
* ``WAKING`` — a wake command was sent; waiting for heartbeat confirmation.
* ``ON`` — sleeper is running; heartbeats are arriving.
* ``FAILED`` — a wake attempt timed out (no heartbeat within ``wake_timeout`` seconds).

State transitions:

* ``OFF`` → ``WAKING``: wake command received.
* ``WAKING`` → ``ON``: heartbeat received within ``wake_timeout``.
* ``WAKING`` → ``FAILED``: no heartbeat within ``wake_timeout``.
* ``ON`` → ``OFF``: suspend command acknowledged, or ``heartbeat_miss_threshold`` consecutive heartbeats missed.
* ``FAILED`` → ``WAKING``: a new wake command is issued.

Heartbeat flow
--------------

The sleeper sends a ``POST /waker/heartbeat`` every ``heartbeat_interval`` seconds (default 60s). After a suspend is requested, heartbeats are suppressed for ``2 × heartbeat_interval`` seconds to prevent the waker from immediately returning to OFF and then re-waking the machine.

Backups
-------

.. code-block:: bash

   sudo cp /etc/sleep-manager/sleep-manager-config.toml /backup/
   sudo cp /etc/systemd/system/sleep-manager.service /backup/
   sudo cp /etc/systemd/system/sleep-manager-delay.service /backup/
