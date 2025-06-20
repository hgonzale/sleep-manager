from flask import request, current_app
from functools import wraps
import logging
import subprocess
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SleepManagerError(Exception):
    """Base exception for sleep manager errors"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ConfigurationError(SleepManagerError):
    """Raised when there's a configuration error"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class SystemCommandError(SleepManagerError):
    """Raised when a system command fails"""
    def __init__(self, message: str, command: str, return_code: int, stderr: str):
        super().__init__(
            message,
            status_code=500,
            details={
                'command': command,
                'return_code': return_code,
                'stderr': stderr
            }
        )


class NetworkError(SleepManagerError):
    """Raised when there's a network-related error"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=503, details=details)


def handle_error(error: Exception) -> tuple[dict, int]:
    """Global error handler for the application"""
    if isinstance(error, SleepManagerError):
        logger.error(f"{error.__class__.__name__}: {error.message}", extra=error.details)
        return {
            'error': {
                'type': error.__class__.__name__,
                'message': error.message,
                'details': error.details
            }
        }, error.status_code
    
    # Handle unexpected errors
    logger.exception("Unexpected error occurred")
    return {
        'error': {
            'type': 'UnexpectedError',
            'message': 'An unexpected error occurred',
            'details': {'error': str(error)}
        }
    }, 500


def require_api_key(f):
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
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config['API_KEY']:
            raise SleepManagerError('Invalid or missing API key', status_code=401)
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
        result = subprocess.run(['which', command], capture_output=True, text=True)
        if result.returncode != 0:
            return {
                'available': False,
                'error': f'Command {command} not found'
            }
        
        # Check if the command is executable
        result = subprocess.run(['test', '-x', result.stdout.strip()], capture_output=True)
        return {
            'available': result.returncode == 0,
            'path': result.stdout.strip() if result.returncode == 0 else None,
            'error': None if result.returncode == 0 else f'Command {command} is not executable'
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        } 