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

   # Sleeper status
   curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status

   # Waker status (proxy to sleeper)
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status

   # Wake the sleeper
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

   # Suspend the sleeper via the waker
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

   # Suspend + wake workflow
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend
   sleep 10
   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

Backups
-------

.. code-block:: bash

   sudo cp /etc/sleep-manager/sleep-manager-config.toml /backup/
   sudo cp /etc/systemd/system/sleep-manager.service /backup/
   sudo cp /etc/systemd/system/sleep-manager-delay.service /backup/
