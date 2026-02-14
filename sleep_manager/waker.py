import logging
import subprocess
from typing import Any

import requests
from flask import Blueprint, current_app, request

from .core import ConfigurationError, SystemCommandError, require_api_key
from .sleeper import sleeper_url

logger = logging.getLogger(__name__)

waker_bp = Blueprint("waker", __name__, url_prefix="/waker")


def _get_state_machine():
    return current_app.extensions["state_machine"]


def _homekit_value(state_value: str) -> str:
    if state_value == "ON":
        return "on"
    elif state_value == "FAILED":
        return "failed"
    return "off"


@waker_bp.get("/config")
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
    return dict(current_app.config["WAKER"])


@waker_bp.get("/wake")
@require_api_key
def wake() -> dict[str, Any]:
    """Send Wake-on-LAN packet to wake the sleeper machine.

    Sends a Wake-on-LAN (WoL) packet to the sleeper machine using the configured
    etherwake command. Updates the state machine to WAKING.

    **Authentication**: Required (X-API-Key header)

    **Response**:
        A JSON object confirming the wake operation and containing command details.

    **Response Format**:
        .. code-block:: json

            {
                "op": "wake",
                "state": "WAKING",
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

    **Example Usage**:
        .. code-block:: bash

            curl -H "X-API-Key: your-api-key" \
                 -X GET http://waker_url:51339/waker/wake
    """
    sleeper_mac: str = ""
    wol_exec: str = ""
    try:
        sleeper_name: str = current_app.config["SLEEPER"]["name"]
        sleeper_mac = current_app.config["SLEEPER"]["mac_address"]
        wol_exec = current_app.config["WAKER"]["wol_exec"]

        logger.info("Attempting to wake %s using %s (MAC redacted)", sleeper_name, wol_exec)

        # run wake command and get return_code
        _res: subprocess.CompletedProcess[str] = subprocess.run(
            ["sudo", wol_exec, sleeper_mac], capture_output=True, text=True
        )

        if _res.returncode != 0:
            raise SystemCommandError(
                "Wake command failed",
                command=f"{wol_exec} {sleeper_mac}",
                return_code=_res.returncode,
                stderr=_res.stderr,
            )

        sm = _get_state_machine()
        new_state = sm.wake_requested()

        logger.info("Successfully sent wake command to %s, state=%s", sleeper_name, new_state.value)
        return {
            "op": "wake",
            "state": new_state.value,
            "sleeper": {
                "name": sleeper_name,
                "mac_address": sleeper_mac,
            },
            "subprocess": {
                "args": _res.args,
                "returncode": _res.returncode,
                "stdout": _res.stdout,
                "stderr": _res.stderr,
            },
        }
    except KeyError as e:
        missing_key = e.args[0] if e.args else "unknown"
        raise ConfigurationError(f"Missing configuration: {missing_key}") from e
    except SystemCommandError:
        raise
    except Exception:
        logger.exception("Failed to wake sleeper")
        raise SystemCommandError(
            "Failed to wake sleeper",
            command=f"{wol_exec} {sleeper_mac}",
            return_code=-1,
            stderr="command failed",
        ) from None


@waker_bp.get("/suspend")
@require_api_key
def suspend() -> dict[str, Any]:
    """Proxy suspend request to the sleeper machine.

    Proxies a suspend request to the sleeper machine. Logs suspend intent;
    state naturally transitions ON -> OFF via missed heartbeats.

    **Authentication**: Required (X-API-Key header)

    **Response**:
        A JSON object containing the sleeper's response to the suspend request.

    **HTTP Status Codes**:
        - 200: Success (sleeper responded successfully)
        - 401: Unauthorized (missing or invalid API key)
        - 408: Request Timeout (sleeper did not respond in time)
        - 503: Service Unavailable (network error communicating with sleeper)

    **Example Usage**:
        .. code-block:: bash

            curl -H "X-API-Key: your-api-key" \
                 -X GET http://waker_url:51339/waker/suspend
    """
    sm = _get_state_machine()
    sm.suspend_requested()
    return sleeper_request("suspend")


@waker_bp.get("/status")
@require_api_key
def status() -> dict[str, Any]:
    """Return the current state machine state.

    Returns the waker's view of sleeper state, driven by heartbeats.
    Does not probe the sleeper live.

    **Authentication**: Required (X-API-Key header)

    **Response Format**:
        .. code-block:: json

            {
                "op": "status",
                "state": "ON",
                "homekit": "on"
            }

    ``homekit`` values:
        - ``"on"``     — state is ON
        - ``"off"``    — state is OFF or WAKING
        - ``"failed"`` — state is FAILED

    **HTTP Status Codes**:
        - 200: Success
        - 401: Unauthorized (missing or invalid API key)

    **Example Usage**:
        .. code-block:: bash

            curl -H "X-API-Key: your-api-key" \
                 http://waker_url:51339/waker/status
    """
    sm = _get_state_machine()
    state = sm.get_state()
    return {
        "op": "status",
        "state": state.value,
        "homekit": _homekit_value(state.value),
    }


@waker_bp.post("/heartbeat")
@require_api_key
def heartbeat() -> dict[str, Any]:
    """Receive a heartbeat from the sleeper machine.

    Called by the sleeper daemon periodically to signal it is alive.
    Drives the state machine: WAKING/OFF/FAILED -> ON, refreshes ON.

    **Authentication**: Required (X-API-Key header)

    **Response Format**:
        .. code-block:: json

            {"op": "heartbeat", "state": "ON"}

    **HTTP Status Codes**:
        - 200: Success
        - 401: Unauthorized (missing or invalid API key)

    **Example Usage**:
        .. code-block:: bash

            curl -H "X-API-Key: your-api-key" \
                 -X POST http://waker_url:51339/waker/heartbeat
    """
    sm = _get_state_machine()
    new_state = sm.heartbeat_received()
    logger.info("Heartbeat received, state=%s", new_state.value)
    return {"op": "heartbeat", "state": new_state.value}


def waker_url() -> str:
    """Generate the waker URL for network communication.

    Constructs the full URL for the waker machine based on configuration.

    Returns:
        str: The complete waker URL (e.g., "http://waker_url.localdomain:51339/waker")

    Raises:
        ConfigurationError: If required configuration is missing
    """
    try:
        waker_name = current_app.config["WAKER"]["name"]
        domain = current_app.config["COMMON"]["domain"]
        port = current_app.config["COMMON"]["port"]

        return f"http://{waker_name}.{domain}:{port}/waker"
    except KeyError as e:
        missing_key = e.args[0] if e.args else "unknown"
        raise ConfigurationError(f"Missing configuration: {missing_key}") from e


def sleeper_request(endpoint: str) -> dict[str, Any]:
    """Make a request to the sleeper machine.

    Args:
        endpoint: The sleeper endpoint to request (e.g., 'status', 'suspend')

    Returns:
        dict: The sleeper's response wrapped in a standardized format, or an error
              response if the sleeper is down/unavailable

    Raises:
        ConfigurationError: If required configuration is missing
    """
    try:
        url = sleeper_url()
        # max value 3.05 is slightly larger than 3 (TCP response window)
        request_timeout = max(current_app.config["COMMON"]["default_request_timeout"], 3.05)
        logger.info(f"Making request to sleeper at {url}/{endpoint}")

        _res: requests.Response = requests.get(
            f"{url}/{endpoint}",
            timeout=request_timeout,
            headers={"X-API-Key": current_app.config["COMMON"]["api_key"]},
        )

        _json = {}

        # Handle response status
        if _res.status_code == 408:
            logger.warning(f"Request to sleeper timed out for {endpoint}")
            return {
                "op": endpoint,
                "sleeper_status": "down",
                "error": "Sleeper machine is not reachable",
                "details": "Request to sleeper timed out",
            }
        elif not _res.ok:
            logger.warning(f"Sleeper responded with error code {_res.status_code} for {endpoint}")
            return {
                "op": endpoint,
                "sleeper_status": "error",
                "error": f"Sleeper responded with error code {_res.status_code}",
                "details": _res.text,
            }
        else:
            _json = _res.json()

        logger.info(f"Successfully received response from sleeper for {endpoint}")
        return {
            "op": endpoint,
            "sleeper_response": {
                "status_code": _res.status_code,
                "json": _json,
                "text": _res.text,
                "url": _res.url,
            },
        }
    except requests.exceptions.Timeout:
        logger.warning(f"Request to sleeper timed out for {endpoint}")
        return {
            "op": endpoint,
            "sleeper_status": "down",
            "error": "Sleeper machine is not reachable",
            "details": "Request to sleeper timed out",
        }
    except requests.exceptions.ConnectionError:
        logger.warning(f"Failed to connect to sleeper for {endpoint}")
        return {
            "op": endpoint,
            "sleeper_status": "down",
            "error": "Sleeper machine is not reachable",
            "details": "Connection refused - sleeper may be down or sleeping",
        }
    except requests.exceptions.RequestException:
        logger.warning("Network error communicating with sleeper for %s", endpoint)
        return {
            "op": endpoint,
            "sleeper_status": "down",
            "error": "Sleeper machine is not reachable",
            "details": "Network error",
        }
    except Exception:
        logger.exception("Unexpected error during sleeper request for %s", endpoint)
        return {
            "op": endpoint,
            "sleeper_status": "error",
            "error": "Unexpected error occurred",
            "details": "Unexpected error",
        }
