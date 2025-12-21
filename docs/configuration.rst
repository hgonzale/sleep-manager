Configuration
=============

Sleep Manager loads configuration from JSON. The default path is:

``/usr/local/sleep-manager/config/sleep-manager-config.json``

You can override this path with the ``SLEEP_MANAGER_CONFIG_PATH`` environment
variable.

Example configuration
---------------------

.. code-block:: json

   {
       "DOMAIN": "localdomain",
       "PORT": 51339,
       "DEFAULT_REQUEST_TIMEOUT": 4,
       "API_KEY": "your-secure-api-key-here",
       "WAKER": {
           "name": "waker_url",
           "wol_exec": "/usr/sbin/etherwake"
       },
       "SLEEPER": {
           "name": "sleeper_url",
           "mac_address": "AA:BB:CC:DD:EE:FF",
           "systemctl_command": "/usr/bin/systemctl",
           "suspend_verb": "suspend",
           "status_verb": "is-system-running"
       }
   }

Key settings
------------

* ``API_KEY``: Required. Shared secret for all authenticated endpoints.
* ``DOMAIN``: DNS domain used to build machine URLs.
* ``PORT``: HTTP port used by both machines (default 51339).
* ``DEFAULT_REQUEST_TIMEOUT``: Timeout (seconds) for waker -> sleeper requests.

Waker settings (``WAKER``)
--------------------------

* ``name``: Hostname used to build the waker URL.
* ``wol_exec``: Path to the ``etherwake`` executable.

Sleeper settings (``SLEEPER``)
------------------------------

* ``name``: Hostname used to build the sleeper URL.
* ``mac_address``: MAC address used for Wake-on-LAN.
* ``systemctl_command``: Path to ``systemctl``.
* ``suspend_verb``: Verb passed to systemctl to suspend.
* ``status_verb``: Verb passed to systemctl to read status.

Security notes
--------------

* Treat the API key as a secret. Do not commit it to version control.
* Keep Sleep Manager behind a trusted LAN or firewall.
