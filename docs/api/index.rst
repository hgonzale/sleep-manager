API Reference
=============

The Sleep Manager provides a comprehensive REST API for managing sleep/wake cycles between machines. All endpoints return JSON responses and use standard HTTP status codes.

Base URL
--------

All API endpoints are relative to the base URL:

.. code-block:: text

   http://{hostname}:51339

Authentication
--------------

Most API endpoints require authentication using an API key header:

.. code-block:: text

   X-API-Key: your-secure-api-key-here

The following endpoints do not require authentication:

* ``GET /`` - Welcome message
* ``GET /health`` - Health check

Response Format
---------------

All API responses are in JSON format. Successful responses have HTTP status codes in the 200 range. Error responses include an ``error`` object with details about the failure.

Success response format:

.. code-block:: json

   {
       "op": "operation_name",
       "data": { ... }
   }

Error response format:

.. code-block:: json

   {
       "error": {
           "type": "ErrorClassName",
           "message": "Human readable error message",
           "details": {
               "additional": "error details"
           }
       }
   }

HTTP Status Codes
-----------------

* ``200`` — Success
* ``401`` — Unauthorized (missing or invalid API key)
* ``404`` — Not Found
* ``408`` — Request Timeout (waker could not reach sleeper)
* ``500`` — Internal Server Error
* ``503`` — Service Unavailable

Sleeper Endpoints
-----------------

.. toctree::
   :maxdepth: 2

   sleeper

Waker Endpoints
---------------

.. toctree::
   :maxdepth: 2

   waker

Error Types
-----------

.. toctree::
   :maxdepth: 2

   errors

Usage Examples
--------------

.. toctree::
   :maxdepth: 2

   examples 