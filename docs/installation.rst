Installation
============

Prerequisites
-------------

* Debian 12 (Bookworm) or compatible Linux distribution with systemd
* Python 3.11+
* Root/sudo access on both machines
* Wake-on-LAN capable NIC on the sleeper machine
* ``etherwake`` and ``ethtool`` installed

Debian Package Installation
---------------------------

Add the `honkeandpastrami apt repository <https://github.com/honkeandpastrami/debian-repo>`_ and install; ``apt upgrade`` picks up new releases:

.. code-block:: bash

   sudo curl -fsSLo /etc/apt/keyrings/honkeandpastrami.pgp https://honkeandpastrami.github.io/debian-repo/honkeandpastrami.pgp
   printf 'Types: deb\nURIs: https://honkeandpastrami.github.io/debian-repo\nSuites: stable\nComponents: main\nSigned-By: /etc/apt/keyrings/honkeandpastrami.pgp\n' \
     | sudo tee /etc/apt/sources.list.d/honkeandpastrami.sources
   sudo apt update && sudo apt install sleep-manager

Edit the config file (see :doc:`configuration` for all options):

.. code-block:: bash

   sudo nano /etc/sleep-manager/sleep-manager-config.toml

Start and enable the service:

.. code-block:: bash

   sudo systemctl start sleep-manager
   sudo systemctl enable sleep-manager

Manual Installation
-------------------

Install Python and system dependencies:

.. code-block:: bash

   sudo apt update
   sudo apt install python3 python3-venv python3-pip etherwake ethtool

Create the application user and directory:

.. code-block:: bash

   sudo mkdir -p /usr/lib/sleep-manager
   sudo useradd --system --user-group --shell /bin/false sleep-manager

Copy application files:

.. code-block:: bash

   sudo cp -r . /usr/lib/sleep-manager/
   sudo chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager

Create a virtual environment and install:

.. code-block:: bash

   sudo -u sleep-manager python3 -m venv /usr/lib/sleep-manager/venv
   sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install -e /usr/lib/sleep-manager

Install systemd services:

.. code-block:: bash

   sudo cp systemd/sleep-manager.service /etc/systemd/system/
   sudo cp systemd/sleep-manager-delay.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable sleep-manager

Then create and edit the config file as above. See :doc:`configuration` for all options.

Wake-on-LAN setup (sleeper)
---------------------------

1. Enter BIOS/UEFI during boot (often F2, F10, or Del).
2. Enable Wake-on-LAN (may be labeled "Power on by PCI-E").
3. Save and reboot.

Enable WoL on the NIC via NetworkManager:

.. code-block:: bash

   nmcli connection modify <connection-name> 802-3-ethernet.wake-on-lan magic

Or manually with ethtool:

.. code-block:: bash

   sudo ethtool -s <iface> wol g

Packaging (Build the .deb)
--------------------------

Install build dependencies:

.. code-block:: bash

   sudo apt update
   sudo apt install build-essential debhelper-compat rsync dpkg-dev python3-hatchling python3-hatch-vcs

Build the package:

.. code-block:: bash

   ./scripts/build-deb.sh

For operations and troubleshooting, see :doc:`operations` and :doc:`troubleshooting`.
