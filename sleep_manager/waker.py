from flask import Blueprint, current_app
import json
import requests
import subprocess
from typing import Any, Optional
import logging
from .core import require_api_key, ConfigurationError, SystemCommandError, NetworkError
from .sleeper import sleeper_url

logger = logging.getLogger(__name__)

waker_bp = Blueprint('waker', __name__, url_prefix='/waker')


@waker_bp.get('/config')
@require_api_key
def print_config() -> dict[str, Any]:
    """Get waker configuration.
    
    Returns the current configuration of the waker machine. This includes
    waker-specific configuration parameters.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object containing the waker configuration.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "name": "waker_url",
                "wol_exec": "/usr/sbin/etherwake"
            }
            
    **HTTP Status Codes**:
        - 200: Success
        - 401: Unauthorized (missing or invalid API key)
        - 500: Internal Server Error (configuration error)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 500 Internal Server Error: Configuration error
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 http://waker_url:51339/waker/config
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "name": "waker_url",
                "wol_exec": "/usr/sbin/etherwake"
            }
    """
    return current_app.config['WAKER']


@waker_bp.get('/wake')
@require_api_key
def wake() -> dict[str, Any]:
    """Send Wake-on-LAN packet to wake the sleeper machine.
    
    Sends a Wake-on-LAN (WoL) packet to the sleeper machine using the configured
    etherwake command. This will attempt to wake the sleeper machine from a
    suspended state.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object confirming the wake operation and containing command details.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "wake",
                "sleeper": {
                    "name": "sleeper_url",
                    "mac_address": "30:9c:23:1a:e8:e9"
                },
                "subprocess": {
                    "args": ["/usr/sbin/etherwake", "30:9c:23:1a:e8:e9"],
                    "returncode": 0,
                    "stdout": "",
                    "stderr": ""
                }
            }
            
    **HTTP Status Codes**:
        - 200: Success (wake packet sent)
        - 401: Unauthorized (missing or invalid API key)
        - 500: Internal Server Error (wake command failed)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 500 Internal Server Error: Wake-on-LAN command failed
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 -X GET http://waker_url:51339/waker/wake
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "op": "wake",
                "sleeper": {
                    "name": "sleeper_url",
                    "mac_address": "30:9c:23:1a:e8:e9"
                },
                "subprocess": {
                    "args": ["/usr/sbin/etherwake", "30:9c:23:1a:e8:e9"],
                    "returncode": 0,
                    "stdout": "",
                    "stderr": ""
                }
            }
    """
    try:
        sleeper_name = current_app.config['SLEEPER']['name']
        sleeper_mac = current_app.config['SLEEPER']['mac_address']
        wol_exec = current_app.config['WAKER']['wol_exec']

        logger.info(f"Attempting to wake {sleeper_name} using {wol_exec} {sleeper_mac}")

        # run wake command and get return_code
        _res = subprocess.run([wol_exec, sleeper_mac], capture_output=True, text=True)

        if _res.returncode != 0:
            raise SystemCommandError(
                "Wake command failed",
                command=f"{wol_exec} {sleeper_mac}",
                return_code=_res.returncode,
                stderr=_res.stderr
            )

        logger.info(f"Successfully sent wake command to {sleeper_name}")
        return {
            'op': 'wake',
            'sleeper': {
                'name': sleeper_name,
                'mac_address': sleeper_mac,
            },
            'subprocess': {
                'args': _res.args,
                'returncode': _res.returncode,
                'stdout': _res.stdout,
                'stderr': _res.stderr,
            }
        }
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")
    except SystemCommandError:
        raise
    except Exception as e:
        logger.exception("Failed to wake sleeper")
        raise SystemCommandError(
            "Failed to wake sleeper",
            command=f"{wol_exec} {sleeper_mac}",
            return_code=-1,
            stderr=str(e)
        )


@waker_bp.get('/suspend')
@require_api_key
def suspend() -> dict[str, Any]:
    """Proxy suspend request to the sleeper machine.
    
    Proxies a suspend request to the sleeper machine and returns the response.
    This allows the waker to control the sleeper's suspend operation remotely.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object containing the sleeper's response to the suspend request.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "suspend",
                "sleeper_response": {
                    "status_code": 200,
                    "json": {
                        "op": "suspend",
                        "subprocess": {
                            "args": ["/usr/bin/systemctl", "suspend"]
                        }
                    },
                    "text": "{\"op\": \"suspend\", \"subprocess\": {\"args\": [\"/usr/bin/systemctl\", \"suspend\"]}}",
                    "url": "http://sleeper_url.localdomain:51339/sleeper/suspend"
                }
            }
            
    **HTTP Status Codes**:
        - 200: Success (sleeper responded successfully)
        - 401: Unauthorized (missing or invalid API key)
        - 408: Request Timeout (sleeper did not respond in time)
        - 503: Service Unavailable (network error communicating with sleeper)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 408 Request Timeout: Sleeper machine did not respond in time
        - 503 Service Unavailable: Network error communicating with sleeper
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 -X GET http://waker_url:51339/waker/suspend
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "op": "suspend",
                "sleeper_response": {
                    "status_code": 200,
                    "json": {
                        "op": "suspend",
                        "subprocess": {
                            "args": ["/usr/bin/systemctl", "suspend"]
                        }
                    },
                    "text": "{\"op\": \"suspend\", \"subprocess\": {\"args\": [\"/usr/bin/systemctl\", \"suspend\"]}}",
                    "url": "http://sleeper_url.localdomain:51339/sleeper/suspend"
                }
            }
    """
    return sleeper_request('suspend')


@waker_bp.get('/status')
@require_api_key
def status() -> dict[str, Any]:
    """Proxy status request to the sleeper machine.
    
    Proxies a status request to the sleeper machine and returns the response.
    This allows the waker to check the sleeper's system status remotely.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object containing the sleeper's response to the status request.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "status",
                "sleeper_response": {
                    "status_code": 200,
                    "json": {
                        "op": "status",
                        "status": "running",
                        "subprocess": {
                            "returncode": 0,
                            "stdout": "running",
                            "stderr": ""
                        }
                    },
                    "text": "{\"op\": \"status\", \"status\": \"running\"}",
                    "url": "http://sleeper_url.localdomain:51339/sleeper/status"
                }
            }
            
    **HTTP Status Codes**:
        - 200: Success (sleeper responded successfully)
        - 401: Unauthorized (missing or invalid API key)
        - 408: Request Timeout (sleeper did not respond in time)
        - 503: Service Unavailable (network error communicating with sleeper)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 408 Request Timeout: Sleeper machine did not respond in time
        - 503 Service Unavailable: Network error communicating with sleeper
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 -X GET http://waker_url:51339/waker/status
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "op": "status",
                "sleeper_response": {
                    "status_code": 200,
                    "json": {
                        "op": "status",
                        "status": "running",
                        "subprocess": {
                            "returncode": 0,
                            "stdout": "running",
                            "stderr": ""
                        }
                    },
                    "text": "{\"op\": \"status\", \"status\": \"running\"}",
                    "url": "http://sleeper_url.localdomain:51339/sleeper/status"
                }
            }
    """
    return sleeper_request('status')


def waker_url() -> str:
    """Generate the waker URL for network communication.
    
    Constructs the full URL for the waker machine based on configuration.
    This is used for self-referencing and potential future features.
    
    Returns:
        str: The complete waker URL (e.g., "http://waker_url.localdomain:51339/waker")
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    try:
        waker_name = current_app.config['WAKER']['name']
        domain = current_app.config['DOMAIN']
        port = current_app.config['PORT']

        return f'http://{waker_name}.{domain}:{port}/waker'
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")


def sleeper_request(endpoint: str) -> dict[str, Any]:
    """Make a request to the sleeper machine.
    
    Internal function to make HTTP requests to the sleeper machine. This function
    handles authentication, timeouts, and error handling for sleeper communication.
    
    Args:
        endpoint: The sleeper endpoint to request (e.g., 'status', 'suspend')
        
    Returns:
        dict: The sleeper's response wrapped in a standardized format
        
    Raises:
        NetworkError: If there are network communication issues
        ConfigurationError: If required configuration is missing
        
    **Request Details**:
        - Uses the configured API key for authentication
        - Applies timeout based on DEFAULT_REQUEST_TIMEOUT configuration
        - Handles various network error conditions
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "endpoint_name",
                "sleeper_response": {
                    "status_code": 200,
                    "json": { ... },
                    "text": "...",
                    "url": "http://sleeper_url.localdomain:51339/sleeper/endpoint"
                }
            }
    """
    try:
        url = sleeper_url()
        request_timeout = max(current_app.config['DEFAULT_REQUEST_TIMEOUT'], 3.05)  # slightly larger than 3=TCP response window

        logger.info(f"Making request to sleeper at {url}/{endpoint}")

        _res = requests.get(
            f'{url}/{endpoint}',
            timeout=request_timeout,
            headers={'X-API-Key': current_app.config['API_KEY']}
        )

        _timeout = False
        _json = {}
        
        # Handle response status
        if _res.status_code == 408:
            _timeout = True
            raise NetworkError("Request to sleeper timed out")
        elif not _res.ok:
            raise NetworkError(
                f"Sleeper responded with error code {_res.status_code}",
                details={'response': _res.text}
            )
        else:
            _json = _res.json()

        logger.info(f"Successfully received response from sleeper for {endpoint}")
        return {
            'op': endpoint,
            'sleeper_response': {
                'status_code': _res.status_code,
                'json': _json,
                'text': _res.text,
                'url': _res.url,
            }
        }
    except requests.exceptions.Timeout:
        logger.error("Request to sleeper timed out")
        raise NetworkError("Request to sleeper timed out")
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to communicate with sleeper")
        raise NetworkError(f"Failed to communicate with sleeper: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error during sleeper request")
        raise NetworkError(f"Unexpected error: {str(e)}")
