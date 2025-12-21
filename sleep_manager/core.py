import logging
import re
import subprocess
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from flask import current_app, request
from werkzeug.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_P = ParamSpec("_P")
_R = TypeVar("_R")


class SleepManagerError(Exception):
    """Base exception for sleep manager errors"""

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ConfigurationError(SleepManagerError):
    """Raised when there's a configuration error"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=500, details=details)


class SystemCommandError(SleepManagerError):
    """Raised when a system command fails"""

    def __init__(self, message: str, command: str, return_code: int, stderr: str):
        super().__init__(
            message,
            status_code=500,
            details={"command": command, "return_code": return_code, "stderr": stderr},
        )


class NetworkError(SleepManagerError):
    """Raised when there's a network-related error"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=503, details=details)

def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", "xx:xx:xx:xx:xx:xx", value)
    return value


def _sanitize_error_details(details: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in details.items():
        if key in {"stderr"}:
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = _redact_value(value)
    return sanitized


def handle_error(error: Exception) -> tuple[dict[str, Any], int]:
    """Global error handler for the application"""
    if isinstance(error, NotFound):
        return {
            "error": {
                "type": "NotFound",
                "message": "The requested URL was not found on the server.",
            }
        }, 404
    if isinstance(error, SleepManagerError):
        sanitized_details = _sanitize_error_details(error.details)
        logger.error(f"{error.__class__.__name__}: {error.message}", extra=sanitized_details)
        return {
            "error": {
                "type": error.__class__.__name__,
                "message": error.message,
                "details": sanitized_details,
            }
        }, error.status_code
    # Handle unexpected errors
    logger.exception("Unexpected error occurred")
    return {
        "error": {
            "type": "UnexpectedError",
            "message": "An unexpected error occurred",
            "details": {"error": "Unexpected error"},
        }
    }, 500


def require_api_key(f: Callable[_P, _R]) -> Callable[_P, _R]:
    """Decorator to require API key authentication for protected endpoints.

    This decorator checks for the presence of a valid API key in the request headers.
    The API key must be provided in the 'X-API-Key' header and must match the
    configured API_KEY in the application configuration.

    Args:
        f: The function to decorate

    Returns:
        The decorated function

    Raises:
        SleepManagerError: If the API key is missing or invalid (401 status code)
    """

    @wraps(f)
    def decorated_function(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != current_app.config["API_KEY"]:
            raise SleepManagerError("Invalid or missing API key", status_code=401)
        return f(*args, **kwargs)

    return decorated_function


def check_command_availability(command: str) -> dict[str, Any]:
    """Check if a system command is available and executable.

    Args:
        command: The command to check (e.g., 'systemctl', 'etherwake')

    Returns:
        A dictionary containing:
            - available: Boolean indicating if the command is available
            - path: The full path to the command (if available)
            - error: Error message if the command is not available
    """
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(["which", command], capture_output=True, text=True)
        if result.returncode != 0:
            return {"available": False, "error": f"Command {command} not found"}

        command_path = result.stdout.strip()

        # Check if the command is executable
        check_result: subprocess.CompletedProcess[str] = subprocess.run(
            ["test", "-x", command_path], capture_output=True, text=True
        )
        is_executable = check_result.returncode == 0
        return {
            "available": is_executable,
            "path": command_path if is_executable else None,
            "error": None if is_executable else f"Command {command} is not executable",
        }
    except Exception:
        logger.exception("Command availability check failed for %s", command)
        return {"available": False, "error": "Command availability check failed"}
