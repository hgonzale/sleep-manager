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
