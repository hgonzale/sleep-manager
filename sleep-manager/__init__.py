from flask import Flask, json, request, abort, current_app, jsonify
from functools import wraps
import logging
import subprocess
from typing import Any, Optional
from .waker import waker_bp
from .sleeper import sleeper_bp


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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config['API_KEY']:
            raise SleepManagerError('Invalid or missing API key', status_code=401)
        return f(*args, **kwargs)
    return decorated_function


def check_command_availability(command: str) -> dict[str, Any]:
    """Check if a system command is available and executable"""
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


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_file('config/sleep-manager-config.json', load=json.load, text=True)

    # Register error handlers
    app.register_error_handler(SleepManagerError, handle_error)
    app.register_error_handler(Exception, handle_error)

    # Register blueprints with authentication
    app.register_blueprint(waker_bp)
    app.register_blueprint(sleeper_bp)

    @app.route('/')
    def welcome():
        return 'Welcome to sleep manager!'

    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint"""
        health_status = {
            'status': 'healthy',
            'version': '1.0.0',  # You might want to get this from your package
            'components': {}
        }

        # Check configuration
        try:
            required_configs = ['DOMAIN', 'PORT', 'API_KEY']
            missing_configs = [key for key in required_configs if key not in app.config]
            if missing_configs:
                health_status['components']['configuration'] = {
                    'status': 'unhealthy',
                    'error': f'Missing required configurations: {", ".join(missing_configs)}'
                }
            else:
                health_status['components']['configuration'] = {
                    'status': 'healthy'
                }
        except Exception as e:
            health_status['components']['configuration'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check system commands based on role
        if 'SLEEPER' in app.config:
            systemctl_cmd = app.config['SLEEPER'].get('systemctl_command', 'systemctl')
            health_status['components']['systemctl'] = check_command_availability(systemctl_cmd)
        elif 'WAKER' in app.config:
            wol_cmd = app.config['WAKER'].get('wol_exec', 'wol')
            health_status['components']['wol'] = check_command_availability(wol_cmd)

        # Check if any component is unhealthy
        if any(comp.get('status') == 'unhealthy' for comp in health_status['components'].values()):
            health_status['status'] = 'unhealthy'

        return jsonify(health_status)

    return app
