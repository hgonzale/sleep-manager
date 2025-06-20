Error Types
===========

The Sleep Manager uses custom exception classes to provide detailed error information. All errors are returned as JSON responses with appropriate HTTP status codes.

Base Error Class
----------------

.. autoclass:: sleep_manager.core.SleepManagerError
   :members:
   :undoc-members:

Configuration Error
-------------------

.. autoclass:: sleep_manager.core.ConfigurationError
   :members:
   :undoc-members:

System Command Error
--------------------

.. autoclass:: sleep_manager.core.SystemCommandError
   :members:
   :undoc-members:

Network Error
-------------

.. autoclass:: sleep_manager.core.NetworkError
   :members:
   :undoc-members:

Error Handler
-------------

.. autofunction:: sleep_manager.core.handle_error 