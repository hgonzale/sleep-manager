Operations
==========

Service management
------------------

.. code-block:: bash

   sudo systemctl start sleep-manager-sleeper sleep-manager-waker
   sudo systemctl enable sleep-manager-sleeper sleep-manager-waker
   sudo systemctl stop sleep-manager-sleeper sleep-manager-waker
   sudo systemctl disable sleep-manager-sleeper sleep-manager-waker
   sudo systemctl status sleep-manager-sleeper sleep-manager-waker

Logs
----

.. code-block:: bash

   sudo journalctl -u sleep-manager-sleeper -f
   sudo journalctl -u sleep-manager-waker -f

   sudo journalctl -u sleep-manager-sleeper --since "1 hour ago"
   sudo journalctl -u sleep-manager-waker --since "1 hour ago"

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

   sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
   sudo cp /etc/systemd/system/sleep-manager-*.service /backup/
