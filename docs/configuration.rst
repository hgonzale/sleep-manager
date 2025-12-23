Configuration
=============

Sleep Manager loads configuration from TOML. The default path is:

``/etc/sleep-manager/sleep-manager-config.toml``

You can override this path with the ``SLEEP_MANAGER_CONFIG_PATH`` environment
variable.
Both machines can use the same config content; the only difference should be ``COMMON.ROLE``.
Shared settings live under ``[COMMON]``. Set ``COMMON.ROLE`` to ``waker`` or ``sleeper`` to select behavior.
Only the APIs for that role are exposed. Sleeper machines need ``[COMMON]`` + ``[SLEEPER]``.
Waker machines need ``[COMMON]`` + ``[WAKER]`` + ``[SLEEPER]`` (name + mac_address).

Example configuration
---------------------

.. code-block:: toml

   [COMMON]
   ROLE = "waker"
   DOMAIN = "localdomain"
   PORT = 51339
   DEFAULT_REQUEST_TIMEOUT = 4
   API_KEY = "your-secure-api-key-here"

   [WAKER]
   # Only needed on the waker machine.
   name = "waker_url"
   wol_exec = "/usr/sbin/etherwake"

   [SLEEPER]
   # Required on both machines (waker needs these to wake the sleeper).
   name = "sleeper_url"
   mac_address = "AA:BB:CC:DD:EE:FF"

   # Sleeper-only settings.
   systemctl_command = "/usr/bin/systemctl"
   suspend_verb = "suspend"
   status_verb = "is-system-running"

Key settings
------------

* ``COMMON.ROLE``: Required. Either ``waker`` or ``sleeper``.
* ``COMMON.API_KEY``: Required. Shared secret for all authenticated endpoints.
* ``COMMON.DOMAIN``: DNS domain used to build machine URLs.
* ``COMMON.PORT``: HTTP port used by both machines (default 51339).
* ``COMMON.DEFAULT_REQUEST_TIMEOUT``: Timeout (seconds) for waker -> sleeper requests.

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
