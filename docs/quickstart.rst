Quick Start Guide
================

This guide will get you up and running with Sleep Manager in minutes.

Prerequisites
------------

* Two machines on the same local network
* Debian 12 (or compatible Linux) on both machines
* Root/sudo access on both machines
* Wake-on-LAN capable network interface (sleeper machine)

Step 1: Clone and Setup
-----------------------

1. **Clone the repository**:
   .. code-block:: bash

      git clone <repository-url>
      cd sleep-manager

2. **Make the setup script executable**:
   .. code-block:: bash

      chmod +x scripts/setup-system.sh

Step 2: Setup Machines
----------------------

**On the Sleeper machine** (the one that will be suspended):
.. code-block:: bash

   sudo ./scripts/setup-system.sh sleeper

**On the Waker machine** (the one that will wake the sleeper):
.. code-block:: bash

   sudo ./scripts/setup-system.sh waker

Step 3: Configure the Application
--------------------------------

Create the configuration file:
.. code-block:: bash

   sudo mkdir -p /usr/local/sleep-manager/config
   sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

Add your configuration:
.. code-block:: json

   {
       "WAKER": {
           "name": "waker_url",
           "ip": "192.168.1.100",
           "mac": "00:11:22:33:44:55"
       },
       "SLEEPER": {
           "name": "sleeper_url",
           "ip": "192.168.1.101",
           "mac": "AA:BB:CC:DD:EE:FF"
       },
       "API_KEY": "your-secure-api-key-here"
   }

**Important**: Replace the hostnames, IP addresses, MAC addresses, and API key with your actual values.

Step 4: Start Services
---------------------

**On both machines**:
.. code-block:: bash

   sudo systemctl start sleep-manager-sleeper
   sudo systemctl start sleep-manager-waker

**Enable auto-start**:
.. code-block:: bash

   sudo systemctl enable sleep-manager-sleeper
   sudo systemctl enable sleep-manager-waker

Step 5: Test the Setup
---------------------

1. **Check health status**:
   .. code-block:: bash

      curl http://sleeper_url:51339/health
      curl http://waker_url:51339/health

2. **Test sleeper status**:
   .. code-block:: bash

      curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status

3. **Test wake functionality**:
   .. code-block:: bash

      curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

4. **Test suspend functionality**:
   .. code-block:: bash

      curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

Step 6: Configure Wake-on-LAN (Sleeper Only)
--------------------------------------------

1. **Enter BIOS/UEFI** during boot (usually F2, F10, or Del)
2. **Navigate to Power Management** or Advanced settings
3. **Enable Wake-on-LAN** (may be called "Power on by PCI-E")
4. **Save and exit**

The setup script automatically configures Wake-on-LAN on the network interface, but BIOS/UEFI settings must be enabled manually.

Step 7: Verify Everything Works
------------------------------

1. **Check service status**:
   .. code-block:: bash

      sudo systemctl status sleep-manager-sleeper
      sudo systemctl status sleep-manager-waker

2. **Check Wake-on-LAN status**:
   .. code-block:: bash

      sudo ethtool eth0 | grep -i wake

3. **Test the complete workflow**:
   .. code-block:: bash

      # Suspend the sleeper
      curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend
      
      # Wait a moment, then wake it
      sleep 10
      curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

Troubleshooting
--------------

If something doesn't work:

1. **Check service logs**:
   .. code-block:: bash

      sudo journalctl -u sleep-manager-sleeper -f
      sudo journalctl -u sleep-manager-waker -f

2. **Check system status**:
   .. code-block:: bash

      sudo ./scripts/setup-system.sh status

3. **Verify network connectivity**:
   .. code-block:: bash

      ping sleeper_url
      ping waker_url

For more detailed troubleshooting, see :doc:`troubleshooting`.

Next Steps
----------

Now that you have Sleep Manager running:

1. **Set up automated scripts** for scheduled suspend/wake
2. **Configure monitoring** to track system status
3. **Set up logging** for debugging and auditing
4. **Explore the API** for custom integrations

For detailed API documentation, see :doc:`api/index`.

For advanced configuration options, see :doc:`configuration`. 
