HomeKit Integration
===================

Sleep Manager ships a custom Homebridge plugin (``homebridge-sleep-manager``) that exposes the sleeper as an On/Off switch in Apple Home. Requires Homebridge ≥ 2.0.

How it works
------------

The plugin polls ``GET /waker/status`` on the waker at a configurable interval and maps the state machine state to HomeKit characteristics:

.. list-table::
   :header-rows: 1

   * - State machine state
     - Switch.On
     - StatusFault
   * - ``ON``
     - true
     - NO_FAULT
   * - ``OFF``
     - false
     - NO_FAULT
   * - ``WAKING``
     - false
     - NO_FAULT
   * - ``FAILED``
     - false
     - GENERAL_FAULT

When you toggle the switch **on**, the plugin calls ``GET /waker/wake``. When you toggle it **off**, it calls ``GET /waker/suspend``. The switch state is driven entirely by polling — there is no push from the waker to Homebridge.

The ``FAILED`` state (wake attempt timed out) surfaces as a warning icon in Apple Home via ``StatusFault``. Issuing a new wake command clears it.

Installation
------------

Install the plugin from the ``homebridge-sleep-manager/`` directory in the repository:

.. code-block:: bash

   npm install -g /path/to/homebridge-sleep-manager

Or copy the directory into your Homebridge plugin path and restart Homebridge.

Configuration
-------------

Add an entry to the ``accessories`` array in your Homebridge ``config.json``:

.. code-block:: json

   {
     "accessory": "SleepManagerSwitch",
     "name": "My PC",
     "waker_url": "http://waker_url:51339",
     "api_key": "your-secure-api-key-here",
     "poll_interval": 30
   }

Config keys:

* ``accessory``: Must be ``"SleepManagerSwitch"``.
* ``name``: Display name shown in Apple Home.
* ``waker_url``: Base URL of the waker. Required.
* ``api_key``: The ``common.api_key`` value from the sleep-manager config. Required.
* ``poll_interval``: How often (seconds) to poll ``/waker/status``. Default: ``30``.

Troubleshooting
---------------

Check that the waker is reachable and responding:

.. code-block:: bash

   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
   # Expected: {"op": "status", "state": "OFF", "homekit": "off"}

If the switch is stuck or shows a fault, check the Homebridge log for ``homebridge-sleep-manager`` entries and verify the waker service is running (see :doc:`troubleshooting`).
