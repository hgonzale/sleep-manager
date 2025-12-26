Installation
============

This guide covers installing the Sleep Manager application on Debian 12 systems.

Prerequisites
------------

Before installation, ensure you have:

* **Debian 12 (Bookworm)** or compatible Linux distribution
* **Python 3.11** or higher
* **Root/sudo access** on both machines
* **Network connectivity** between machines
* **Wake-on-LAN capable** network interface (for sleeper)

System Requirements
------------------

* systemd for service management
* Wake-on-LAN capable network interface (sleeper)
* etherwake package installed
* ethtool package installed

Debian Package Installation
---------------------------

Download the latest `.deb` from GitHub Releases and install it:

1. **Install the package**:
   .. code-block:: bash

      sudo dpkg -i sleep-manager_*.deb

2. **Configure the application**:
   .. code-block:: bash

      sudo nano /etc/sleep-manager/sleep-manager-config.toml

3. **Start the service**:
   .. code-block:: bash

      sudo systemctl start sleep-manager
      sudo systemctl enable sleep-manager
      # Both machines can use the same config content.
      # Configure [common] plus the role-specific section(s).
      # The active role is selected by matching the hostname to waker.name or sleeper.name.
      # Only the APIs for the detected role will be exposed.

Manual Installation (Non-Debian Distros)
----------------------------------------

If you are not on Debian, follow the manual steps below.

Manual Installation
-------------------

If you prefer to install manually or need to customize the installation:

1. **Install Python dependencies**:
   .. code-block:: bash

      sudo apt update
      sudo apt install python3 python3-venv python3-pip

2. **Create application directory**:
   .. code-block:: bash

      sudo mkdir -p /usr/lib/sleep-manager
      sudo useradd --system --user-group --shell /bin/false sleep-manager

3. **Copy application files**:
   .. code-block:: bash

      sudo cp -r . /usr/lib/sleep-manager/
      sudo chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager

4. **Create virtual environment**:
   .. code-block:: bash

      cd /usr/lib/sleep-manager
      sudo -u sleep-manager python3 -m venv venv
      sudo -u sleep-manager venv/bin/pip install -e .

5. **Install system dependencies**:
   .. code-block:: bash

      sudo apt install etherwake ethtool

6. **Install systemd services**:
   .. code-block:: bash

      sudo cp systemd/sleep-manager.service /etc/systemd/system/
      sudo cp systemd/sleep-manager-delay.service /etc/systemd/system/
      sudo systemctl daemon-reload
      sudo systemctl enable sleep-manager
      # Configure [common] plus the role-specific section(s).

Configuration
-------------

Create the configuration file:

.. code-block:: bash

   sudo mkdir -p /etc/sleep-manager
   sudo nano /etc/sleep-manager/sleep-manager-config.toml

Example configuration:

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

For detailed configuration options, see :doc:`configuration`.

Wake-on-LAN setup (sleeper)
---------------------------

1. Enter BIOS/UEFI during boot (often F2, F10, or Del).
2. Enable Wake-on-LAN (may be labeled "Power on by PCI-E").
3. Save and reboot.

The setup script configures the NIC for WoL, but BIOS/UEFI support must be enabled manually.

Packaging (Build the .deb)
--------------------------

If you need to build the Debian package locally:

1. **Install build dependencies**:
   .. code-block:: bash

      sudo apt update
      sudo apt install build-essential debhelper-compat rsync dpkg-dev python3-hatchling python3-hatch-vcs

2. **Build the package**:
   .. code-block:: bash

      ./scripts/build-deb.sh

Troubleshooting
--------------

Common installation issues:

1. **Permission denied errors**:
   .. code-block:: bash

      sudo chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager

2. **Service won't start**:
   .. code-block:: bash

      sudo journalctl -u sleep-manager -n 50

3. **Python import errors**:
   .. code-block:: bash

      sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install -e .

For more troubleshooting help, see :doc:`troubleshooting`.

Next Steps
----------

After successful installation:

1. Configure Wake-on-LAN in BIOS/UEFI (sleeper machine)
2. Test the complete workflow
3. Set up monitoring and logging
4. Configure automated scripts

For operational commands, verification, and troubleshooting, see :doc:`operations` and :doc:`troubleshooting`.
