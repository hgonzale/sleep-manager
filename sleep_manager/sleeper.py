from flask import Blueprint, current_app
import requests
import subprocess
from typing import Any
import logging
from .core import require_api_key, ConfigurationError, SystemCommandError

logger = logging.getLogger(__name__)

sleeper_bp = Blueprint('sleeper', __name__, url_prefix='/sleeper')


@sleeper_bp.get('/config')
@require_api_key
def print_config() -> dict[str, Any]:
    """Get sleeper configuration.
    
    Returns the current configuration of the sleeper machine. This includes
    all configuration parameters including the API key (hidden for security).
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object containing the complete sleeper configuration.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "DOMAIN": "localdomain",
                "PORT": 51339,
                "DEFAULT_REQUEST_TIMEOUT": 4,
                "API_KEY": "***hidden***",
                "SLEEPER": {
                    "name": "sleeper_url",
                    "mac_address": "30:9c:23:1a:e8:e9",
                    "systemctl_exec": "/usr/bin/systemctl",
                    "suspend_verb": "suspend",
                    "status_verb": "is-system-running"
                }
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
                 http://sleeper_url:51339/sleeper/config
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "DOMAIN": "localdomain",
                "PORT": 51339,
                "DEFAULT_REQUEST_TIMEOUT": 4,
                "API_KEY": "***hidden***",
                "SLEEPER": {
                    "name": "sleeper_url",
                    "mac_address": "30:9c:23:1a:e8:e9",
                    "systemctl_exec": "/usr/bin/systemctl",
                    "suspend_verb": "suspend",
                    "status_verb": "is-system-running"
                }
            }
    """
    return current_app.config


@sleeper_bp.get('/suspend')
@require_api_key
def suspend() -> dict[str, Any]:
    """Suspend the sleeper machine.
    
    Suspends the sleeper machine using the systemctl suspend command. The system
    will suspend after a short delay to allow the response to be sent. This delay
    is provided by the systemd delay service configured during setup.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object confirming the suspend operation was initiated.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "suspend",
                "subprocess": {
                    "args": ["/usr/bin/systemctl", "suspend"]
                }
            }
            
    **HTTP Status Codes**:
        - 200: Success (suspend initiated)
        - 401: Unauthorized (missing or invalid API key)
        - 500: Internal Server Error (system command failed)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 500 Internal Server Error: System command failed
        
    **Note**: 
        The system will suspend shortly after this response is sent. The response
        may be cut off if the system suspends before it's fully transmitted.
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 -X GET http://sleeper_url:51339/sleeper/suspend
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "op": "suspend",
                "subprocess": {
                    "args": ["/usr/bin/systemctl", "suspend"]
                }
            }
    """
    try:
        systemctl_exec = current_app.config['SLEEPER']['systemctl_command']
        suspend_verb = current_app.config['SLEEPER']['suspend_verb']

        logger.info(f"Attempting to suspend system using {systemctl_exec} {suspend_verb}")

        # Once this command is executed, we have a race between the system suspend
        # and Flask responding the request. We assume that systemd-sleep has been
        # added a pre-suspend service with a delay of ~5 secs, so this Flask has
        # enough time to respond.
        _res = subprocess.Popen([systemctl_exec, suspend_verb])

        logger.info("Suspend command initiated successfully")
        return {
            'op': 'suspend',
            'subprocess': {
                'args': [systemctl_exec, suspend_verb],
            }
        }
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")
    except Exception as e:
        logger.exception("Failed to suspend system")
        raise SystemCommandError(
            "Failed to suspend system",
            command=f"{systemctl_exec} {suspend_verb}",
            return_code=-1,
            stderr=str(e)
        )


@sleeper_bp.get('/status')
@require_api_key
def status() -> dict[str, Any]:
    """Get sleeper system status.
    
    Returns the current system status of the sleeper machine using the systemctl
    is-system-running command. This provides information about whether the system
    is running normally, in maintenance mode, starting, or stopping.
    
    **Authentication**: Required (X-API-Key header)
    
    **Response**:
        A JSON object containing the system status and command execution details.
        
    **Response Format**:
        .. code-block:: json
        
            {
                "op": "status",
                "status": "running",
                "subprocess": {
                    "args": ["/usr/bin/systemctl", "is-system-running"],
                    "returncode": 0,
                    "stdout": "running",
                    "stderr": ""
                }
            }
            
    **Status Values**:
        - ``running``: System is running normally
        - ``maintenance``: System is in maintenance mode
        - ``stopping``: System is shutting down
        - ``starting``: System is starting up
        
    **HTTP Status Codes**:
        - 200: Success
        - 401: Unauthorized (missing or invalid API key)
        - 500: Internal Server Error (system command failed)
        
    **Error Responses**:
        - 401 Unauthorized: Missing or invalid API key
        - 500 Internal Server Error: System command failed
        
    **Example Usage**:
        .. code-block:: bash
            
            curl -H "X-API-Key: your-api-key" \
                 http://sleeper_url:51339/sleeper/status
                 
    **Example Response**:
        .. code-block:: json
        
            {
                "op": "status",
                "status": "running",
                "subprocess": {
                    "args": ["/usr/bin/systemctl", "is-system-running"],
                    "returncode": 0,
                    "stdout": "running",
                    "stderr": ""
                }
            }
    """
    try:
        systemctl_exec = current_app.config['SLEEPER']['systemctl_command']
        status_verb = current_app.config['SLEEPER']['status_verb']

        logger.info(f"Checking system status using {systemctl_exec} {status_verb}")

        # run systemd status command
        _res = subprocess.run([systemctl_exec, status_verb], capture_output=True, text=True)

        if _res.returncode != 0:
            raise SystemCommandError(
                "Status command failed",
                command=f"{systemctl_exec} {status_verb}",
                return_code=_res.returncode,
                stderr=_res.stderr
            )

        logger.info("Status command completed successfully")
        return {
            'op': 'status',
            'status': _res.stdout,
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
        logger.exception("Failed to get system status")
        raise SystemCommandError(
            "Failed to get system status",
            command=f"{systemctl_exec} {status_verb}",
            return_code=-1,
            stderr=str(e)
        )


def sleeper_url() -> str:
    """Generate the sleeper URL for network communication.
    
    Constructs the full URL for the sleeper machine based on configuration.
    This is used by the waker to communicate with the sleeper.
    
    Returns:
        str: The complete sleeper URL (e.g., "http://sleeper_url.localdomain:51339/sleeper")
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    try:
        sleeper_name = current_app.config['SLEEPER']['name']
        domain = current_app.config['DOMAIN']
        port = current_app.config['PORT']

        return f'http://{sleeper_name}.{domain}:{port}/sleeper'
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")
