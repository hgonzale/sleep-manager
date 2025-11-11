Installation
============

This guide covers installing the Sleep Manager application on Debian 12 systems.

Prerequisites
------------

Before installation, ensure you have:

* **Debian 12 (Bookworm)** or compatible Linux distribution
* **Python 3.10** or higher
* **Root/sudo access** on both machines
* **Network connectivity** between machines
* **Wake-on-LAN capable** network interface (for sleeper)

System Requirements
------------------

For detailed system requirements, see :doc:`../SYSTEM_REQUIREMENTS`.

Quick Installation
------------------

1. **Clone the repository**:
   .. code-block:: bash

      git clone <repository-url>
      cd sleep-manager

2. **Make setup script executable**:
   .. code-block:: bash

      chmod +x scripts/setup-system.sh

3. **Setup Sleeper machine**:
   .. code-block:: bash

      sudo ./scripts/setup-system.sh sleeper

4. **Setup Waker machine**:
   .. code-block:: bash

      sudo ./scripts/setup-system.sh waker

5. **Configure the application**:
   .. code-block:: bash

      sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

6. **Start services**:
   .. code-block:: bash

      sudo systemctl start sleep-manager-sleeper
      sudo systemctl start sleep-manager-waker

Manual Installation
-------------------

If you prefer to install manually or need to customize the installation:

1. **Install Python dependencies**:
   .. code-block:: bash

      sudo apt update
      sudo apt install python3 python3-venv python3-pip

2. **Create application directory**:
   .. code-block:: bash

      sudo mkdir -p /usr/local/sleep-manager
      sudo useradd --system --user-group --shell /bin/false sleep-manager

3. **Copy application files**:
   .. code-block:: bash

      sudo cp -r . /usr/local/sleep-manager/
      sudo chown -R sleep-manager:sleep-manager /usr/local/sleep-manager

4. **Create virtual environment**:
   .. code-block:: bash

      cd /usr/local/sleep-manager
      sudo -u sleep-manager python3 -m venv venv
      sudo -u sleep-manager venv/bin/pip install -e .

5. **Install system dependencies**:
   .. code-block:: bash

      # For sleeper
      sudo apt install ethtool

      # For waker
      sudo apt install etherwake

6. **Install systemd services**:
   .. code-block:: bash

      sudo cp systemd/sleep-manager-*.service /etc/systemd/system/
      sudo systemctl daemon-reload
      sudo systemctl enable sleep-manager-sleeper
      sudo systemctl enable sleep-manager-waker

Configuration
-------------

Create the configuration file:

.. code-block:: bash

   sudo mkdir -p /usr/local/sleep-manager/config
   sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

Example configuration:

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

For detailed configuration options, see :doc:`configuration`.

Verification
------------

After installation, verify the setup:

1. **Check service status**:
   .. code-block:: bash

      sudo systemctl status sleep-manager-sleeper
      sudo systemctl status sleep-manager-waker

2. **Test health endpoint**:
   .. code-block:: bash

      curl http://sleeper_url:51339/health
      curl http://waker_url:51339/health

3. **Test API endpoints**:
   .. code-block:: bash

      curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status
      curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

Troubleshooting
--------------

Common installation issues:

1. **Permission denied errors**:
   .. code-block:: bash

      sudo chown -R sleep-manager:sleep-manager /usr/local/sleep-manager

2. **Service won't start**:
   .. code-block:: bash

      sudo journalctl -u sleep-manager-sleeper -n 50

3. **Python import errors**:
   .. code-block:: bash

      sudo -u sleep-manager /usr/local/sleep-manager/venv/bin/pip install -e .

For more troubleshooting help, see :doc:`troubleshooting`.

Next Steps
----------

After successful installation:

1. Configure Wake-on-LAN in BIOS/UEFI (sleeper machine)
2. Test the complete workflow
3. Set up monitoring and logging
4. Configure automated scripts

For detailed usage instructions, see :doc:`quickstart`. 
