Configuration
=============

Sleep Manager loads configuration from TOML. The default path is:

``/etc/sleep-manager/sleep-manager-config.toml``

You can override this path with the ``SLEEP_MANAGER_CONFIG_PATH`` environment
variable.
Both machines can use the same config content; the active role is derived from the
machine hostname matching ``waker.name`` or ``sleeper.name``.
Shared settings live under ``[common]``. Only the APIs for the detected role are exposed.
Sleeper machines need ``[common]`` + ``[sleeper]``.
Waker machines need ``[common]`` + ``[waker]`` + ``[sleeper]`` (name + mac_address).

Example configuration
---------------------

.. code-block:: toml

   [common]
   domain = "localdomain"
   port = 51339
   default_request_timeout = 4
   api_key = "your-secure-api-key-here"

   [waker]
   # Only needed on the waker machine.
   name = "waker_url"
   wol_exec = "/usr/sbin/etherwake"

   [sleeper]
   # Required on both machines (waker needs these to wake the sleeper).
   name = "sleeper_url"
   mac_address = "AA:BB:CC:DD:EE:FF"

   # Sleeper-only settings.
   systemctl_command = "/usr/bin/systemctl"
   suspend_verb = "suspend"
   status_verb = "is-system-running"

Key settings
------------

* ``common.api_key``: Required. Shared secret for all authenticated endpoints.
* ``common.domain``: DNS domain used to build machine URLs.
* ``common.port``: HTTP port used by both machines (default 51339).
* ``common.default_request_timeout``: Timeout (seconds) for waker -> sleeper requests.

Waker settings (``waker``)
--------------------------

* ``name``: Hostname used to build the waker URL.
* ``wol_exec``: Path to the ``etherwake`` executable.

Sleeper settings (``sleeper``)
------------------------------

* ``name``: Hostname used to build the sleeper URL.
* ``mac_address``: MAC address used for Wake-on-LAN.
* ``systemctl_command``: Path to ``systemctl``.
* ``suspend_verb``: Verb passed to systemctl to suspend.
* ``status_verb``: Verb passed to systemctl to read status.

Role selection
--------------

Sleep Manager selects the role based on the machine hostname. If the hostname matches
``waker.name`` (or ``waker.name`` + ``common.domain``), the waker APIs are enabled. If it
matches ``sleeper.name`` (or ``sleeper.name`` + ``common.domain``), the sleeper APIs are enabled.

Security notes
--------------

* Treat the API key as a secret. Do not commit it to version control.
* Keep Sleep Manager behind a trusted LAN or firewall.
