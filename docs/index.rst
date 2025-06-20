Sleep Manager Documentation
===========================

A Flask-based application for managing sleep/wake cycles between two machines on a local network.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index

Overview
--------

The Sleep Manager consists of two components:

* **Sleeper**: Machine that can be suspended and woken remotely
* **Waker**: Machine that sends Wake-on-LAN packets to wake the sleeper

The system provides a RESTful API for remote control of sleep/wake cycles, with secure authentication and comprehensive error handling.

Features
--------

* **Remote Suspend**: Suspend the sleeper machine via HTTP API
* **Wake-on-LAN**: Wake the sleeper machine remotely
* **Status Monitoring**: Check the status of both machines
* **API Key Authentication**: Secure API access
* **Systemd Integration**: Automatic service management
* **Debian 12 Support**: Optimized for Debian 12 systems

Architecture
------------

.. code-block:: text

   [Waker Machine] ---- [Local Network] ---- [Sleeper Machine]
       (waker_url)                              (sleeper_url)

* **Sleeper**: Runs Flask app on port 51339, can be suspended via API
* **Waker**: Runs Flask app on port 51339, sends Wake-on-LAN packets
* **Communication**: HTTP API with API key authentication

Quick Start
-----------

1. **Setup Sleeper**:
   .. code-block:: bash

      sudo ./scripts/setup-system.sh sleeper

2. **Setup Waker**:
   .. code-block:: bash

      sudo ./scripts/setup-system.sh waker

3. **Configure the application**:
   .. code-block:: bash

      sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

4. **Start services**:
   .. code-block:: bash

      sudo systemctl start sleep-manager-sleeper
      sudo systemctl start sleep-manager-waker

5. **Test the setup**:
   .. code-block:: bash

      curl http://sleeper_url:51339/status
      curl -H "X-API-Key: your-api-key" http://waker_url:51339/wake

For detailed instructions, see :doc:`installation` and :doc:`quickstart`.

API Reference
-------------

The Sleep Manager provides a comprehensive REST API with the following endpoints:

* **Health Check**: ``GET /health`` - Check application health
* **Sleeper Endpoints**: ``/sleeper/*`` - Control sleeper machine
* **Waker Endpoints**: ``/waker/*`` - Control waker operations

For complete API documentation, see :doc:`api/index`.

Installation
------------

The Sleep Manager is designed for Debian 12 systems and requires:

* Python 3.8 or higher
* systemd for service management
* Wake-on-LAN capable network interface (sleeper)
* etherwake package (waker)

For detailed installation instructions, see :doc:`installation`.

Support
-------

For issues and questions:

1. Review the API documentation
2. Check service logs: ``sudo journalctl -u sleep-manager-* -f``
3. Open an issue on the repository

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 