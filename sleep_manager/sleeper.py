import datetime
import logging
import subprocess
import threading
import time
from copy import deepcopy
from typing import Any

import requests
from flask import Blueprint, Flask, current_app

from .core import ConfigurationError, SystemCommandError, require_api_key

logger = logging.getLogger(__name__)

sleeper_bp = Blueprint("sleeper", __name__, url_prefix="/sleeper")


@sleeper_bp.get("/config")
@require_api_key
def print_config() -> dict[str, Any]:
    """Get sleeper configuration (sanitized for JSON serialization and security)."""

    def sanitize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        elif isinstance(obj, bytes):
            try:
                return obj.decode()
            except Exception:
                return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return str(obj)
        return obj

    config = deepcopy(dict(current_app.config))
    # Hide API key
    common = config.get("COMMON")
    if isinstance(common, dict) and "api_key" in common:
        common["api_key"] = "***hidden***"
    # Recursively sanitize
    result = sanitize(config)  # type: ignore
    result["config_checksum"] = current_app.extensions["config_checksum"]
    return result


@sleeper_bp.get("/suspend")
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
    systemctl_exec: str = ""
    suspend_verb: str = ""
    try:
        systemctl_exec = current_app.config["SLEEPER"]["systemctl_command"]
        suspend_verb = current_app.config["SLEEPER"]["suspend_verb"]

        logger.info(f"Attempting to suspend system using sudo {systemctl_exec} {suspend_verb}")

        # Once this command is executed, we have a race between the system suspend
        # and Flask responding the request. We assume that systemd-sleep has been
        # added a pre-suspend service with a delay of ~5 secs, so this Flask has
        # enough time to respond.
        subprocess.Popen(["sudo", systemctl_exec, suspend_verb])

        logger.info("Suspend command initiated successfully")
        return {
            "op": "suspend",
            "subprocess": {
                "args": ["sudo", systemctl_exec, suspend_verb],
            },
        }
    except KeyError as e:
        missing_key = e.args[0] if e.args else "unknown"
        raise ConfigurationError(f"Missing configuration: {missing_key}") from e
    except Exception:
        logger.exception("Failed to suspend system")
        raise SystemCommandError(
            "Failed to suspend system",
            command=f"{systemctl_exec} {suspend_verb}".strip(),
            return_code=-1,
            stderr="command failed",
        ) from None


@sleeper_bp.get("/status")
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
    systemctl_exec: str = ""
    status_verb: str = ""
    try:
        systemctl_exec = current_app.config["SLEEPER"]["systemctl_command"]
        status_verb = current_app.config["SLEEPER"]["status_verb"]

        logger.info(f"Checking system status using sudo {systemctl_exec} {status_verb}")

        # run systemd status command
        _res: subprocess.CompletedProcess[str] = subprocess.run(
            [systemctl_exec, status_verb], capture_output=True, text=True
        )

        if _res.returncode != 0:
            raise SystemCommandError(
                "Status command failed",
                command=f"{systemctl_exec} {status_verb}",
                return_code=_res.returncode,
                stderr=_res.stderr,
            )

        logger.info("Status command completed successfully")
        return {
            "op": "status",
            "status": _res.stdout,
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
        logger.exception("Failed to get system status")
        raise SystemCommandError(
            "Failed to get system status",
            command=f"{systemctl_exec} {status_verb}".strip(),
            return_code=-1,
            stderr="command failed",
        ) from None


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
        sleeper_name = current_app.config["SLEEPER"]["name"]
        domain = current_app.config["COMMON"]["domain"]
        port = current_app.config["COMMON"]["port"]

        return f"http://{sleeper_name}.{domain}:{port}/sleeper"
    except KeyError as e:
        missing_key = e.args[0] if e.args else "unknown"
        raise ConfigurationError(f"Missing configuration: {missing_key}") from e


def _start_heartbeat_sender(app: Flask) -> threading.Thread:
    """Start a daemon thread that periodically POSTs heartbeats to waker.

    The thread runs for the lifetime of the application. Failures are logged
    but retried on the next cycle.

    Args:
        app: The Flask application (used to access config inside the thread).

    Returns:
        The started daemon thread (for testing purposes).
    """

    def _run() -> None:
        with app.app_context():
            interval: float = float(app.config["COMMON"].get("heartbeat_interval", 60))
            waker_name: str = app.config["WAKER"]["name"]
            domain: str = app.config["COMMON"]["domain"]
            port: int = app.config["COMMON"]["port"]
            api_key: str = app.config["COMMON"]["api_key"]
            checksum: str = app.extensions["config_checksum"]
            url = f"http://{waker_name}.{domain}:{port}/waker/heartbeat"

        logger.info("Heartbeat sender started: POSTing to %s every %.0fs", url, interval)

        while True:
            time.sleep(interval)
            try:
                resp = requests.post(
                    url,
                    headers={"X-API-Key": api_key},
                    json={"checksum": checksum},
                    timeout=10,
                )
                resp_data = resp.json()
                if resp_data.get("config_compatible") is False:
                    waker_checksum = resp_data.get("waker_checksum", "unknown")
                    logger.error(
                        "Config mismatch: waker and sleeper configs differ. "
                        "Waker checksum: %s, ours: %s",
                        waker_checksum,
                        checksum,
                    )
                else:
                    logger.debug("Heartbeat sent, waker replied: %s", resp_data)
            except requests.exceptions.RequestException:
                logger.debug("Heartbeat to %s skipped (network unavailable, will retry)", url)
            except Exception:
                logger.warning("Heartbeat POST to %s failed (will retry next cycle)", url, exc_info=True)

    t = threading.Thread(target=_run, daemon=True, name="heartbeat-sender")
    t.start()
    return t
