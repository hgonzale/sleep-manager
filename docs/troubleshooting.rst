Troubleshooting
===============

Service won't start
-------------------

.. code-block:: bash

   sudo systemctl status sleep-manager
   sudo journalctl -u sleep-manager -n 50

Check configuration
-------------------

.. code-block:: bash

   sudo cat /etc/sleep-manager/sleep-manager-config.toml

Common network issues
---------------------

.. code-block:: bash

   ping sleeper_url
   ping waker_url
   nslookup sleeper_url

Wake-on-LAN not working
-----------------------

1. Confirm BIOS/UEFI has Wake-on-LAN enabled.
2. Verify the sleeper NIC supports WoL.
3. Check the NIC settings:

.. code-block:: bash

   sudo ethtool eth0 | grep -i wake

Permission errors
-----------------

.. code-block:: bash

   sudo chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager

State machine stuck or wrong state
-----------------------------------

The waker state machine can be inspected via ``GET /waker/status``:

.. code-block:: bash

   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
   # {"op": "status", "state": "FAILED", "homekit": "off"}

**FAILED state:** A wake attempt timed out. Issue a new ``/waker/wake`` to retry; the state will transition back to WAKING.

**Stuck in WAKING:** The sleeper came up but heartbeats are not reaching the waker. Check network connectivity and verify the sleeper service is running and can reach the waker at ``http://waker_url:<port>/waker/heartbeat``.

**State flaps OFF ↔ ON after suspend:** Expected — the heartbeat suppression window (``2 × heartbeat_interval`` seconds) prevents bounce-back, but if the window is too short for your hardware's resume time, increase ``heartbeat_interval`` in config.

Heartbeat issues
----------------

If the waker logs repeated "missed heartbeat" warnings:

1. Check the sleeper service is running: ``systemctl status sleep-manager`` on the sleeper.
2. Verify the sleeper can reach the waker: ``curl -k http://waker_url:<port>/health``.
3. Check ``heartbeat_miss_threshold`` — the default is 3 missed heartbeats before the waker transitions to OFF.

Config mismatch between machines
---------------------------------

The heartbeat includes a config checksum. If the waker and sleeper are running with different configs, the waker will log a warning. Ensure both machines use identical ``[common]`` and ``[sleeper]`` sections.
