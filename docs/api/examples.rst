Usage Examples
==============

This section provides practical examples of how to use the Sleep Manager API with different programming languages and tools.

Using curl
----------

Check health status:
.. code-block:: bash

   curl http://sleeper_url:51339/health

Get sleeper status:
.. code-block:: bash

   curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status

Wake the sleeper:
.. code-block:: bash

   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

Suspend the sleeper:
.. code-block:: bash

   curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

Using Python requests
--------------------

.. code-block:: python

   import requests

   # Configuration
   API_KEY = "your-api-key"
   SLEEPER_URL = "http://sleeper_url:51339"
   WAKER_URL = "http://waker_url:51339"
   HEADERS = {"X-API-Key": API_KEY}

   # Check health
   response = requests.get(f"{SLEEPER_URL}/health")
   print(response.json())

   # Get sleeper status
   response = requests.get(f"{SLEEPER_URL}/sleeper/status", headers=HEADERS)
   print(response.json())

   # Wake the sleeper
   response = requests.get(f"{WAKER_URL}/waker/wake", headers=HEADERS)
   print(response.json())

   # Suspend the sleeper
   response = requests.get(f"{WAKER_URL}/waker/suspend", headers=HEADERS)
   print(response.json())

Using JavaScript fetch
---------------------

.. code-block:: javascript

   const API_KEY = "your-api-key";
   const SLEEPER_URL = "http://sleeper_url:51339";
   const WAKER_URL = "http://waker_url:51339";
   const headers = { "X-API-Key": API_KEY };

   // Check health
   fetch(`${SLEEPER_URL}/health`)
       .then(response => response.json())
       .then(data => console.log(data));

   // Get sleeper status
   fetch(`${SLEEPER_URL}/sleeper/status`, { headers })
       .then(response => response.json())
       .then(data => console.log(data));

   // Wake the sleeper
   fetch(`${WAKER_URL}/waker/wake`, { headers })
       .then(response => response.json())
       .then(data => console.log(data));

   // Suspend the sleeper
   fetch(`${WAKER_URL}/waker/suspend`, { headers })
       .then(response => response.json())
       .then(data => console.log(data));

Automated Scripts
-----------------

Night-time shutdown script:
.. code-block:: bash

   #!/bin/bash
   # Suspend at 10 PM
   curl -H "X-API-Key: your-api-key" \
        -X GET http://waker_url:51339/waker/suspend

Morning wake-up script:
.. code-block:: bash

   #!/bin/bash
   # Wake at 8 AM
   curl -H "X-API-Key: your-api-key" \
        -X GET http://waker_url:51339/waker/wake

Status monitoring script:
.. code-block:: bash

   #!/bin/bash
   # Check waker state machine state
   STATE=$(curl -s -H "X-API-Key: your-api-key" \
                http://waker_url:51339/waker/status | \
                jq -r '.state')

   if [ "$STATE" = "ON" ]; then
       echo "Sleeper is on"
   elif [ "$STATE" = "FAILED" ]; then
       echo "Wake attempt failed"
   else
       echo "Sleeper is off (state: $STATE)"
   fi

Error Handling
--------------

Python example with error handling:
.. code-block:: python

   import requests
   from requests.exceptions import RequestException

   def wake_sleeper():
       try:
           response = requests.get(
               "http://waker_url:51339/waker/wake",
               headers={"X-API-Key": "your-api-key"},
               timeout=10
           )
           response.raise_for_status()
           return response.json()
       except RequestException as e:
           print(f"Network error: {e}")
           return None
       except Exception as e:
           print(f"Unexpected error: {e}")
           return None

   result = wake_sleeper()
   if result:
       print("Wake command sent successfully")
   else:
       print("Failed to send wake command")

JavaScript example with error handling:
.. code-block:: javascript

   async function wakeSleeper() {
       try {
           const response = await fetch('http://waker_url:51339/waker/wake', {
               headers: { 'X-API-Key': 'your-api-key' }
           });
           
           if (!response.ok) {
               throw new Error(`HTTP error! status: ${response.status}`);
           }
           
           const data = await response.json();
           console.log('Wake command sent successfully:', data);
           return data;
       } catch (error) {
           console.error('Failed to send wake command:', error);
           return null;
       }
   }

   wakeSleeper(); 