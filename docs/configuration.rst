Configuration
=============

Sleep Manager loads configuration from TOML. The default path is:

``/etc/sleep-manager/sleep-manager-config.toml``

You can override this path with the ``SLEEP_MANAGER_CONFIG_PATH`` environment
variable.
Both machines can use the same config content; the only difference should be ``common.role``.
Shared settings live under ``[common]``. Set ``common.role`` to ``waker`` or ``sleeper`` to select behavior.
Only the APIs for that role are exposed. Sleeper machines need ``[common]`` + ``[sleeper]``.
Waker machines need ``[common]`` + ``[waker]`` + ``[sleeper]`` (name + mac_address).

Example configuration
---------------------

.. code-block:: toml

   [common]
   role = "waker"
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

* ``common.role``: Required. Either ``waker`` or ``sleeper``.
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

Security notes
--------------

* Treat the API key as a secret. Do not commit it to version control.
* Keep Sleep Manager behind a trusted LAN or firewall.
