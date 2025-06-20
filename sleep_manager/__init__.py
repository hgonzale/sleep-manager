from flask import Flask, json, request, abort, current_app, jsonify
import logging
import subprocess
from typing import Any, Optional
from .core import (
    SleepManagerError, ConfigurationError, SystemCommandError, NetworkError,
    handle_error, require_api_key, check_command_availability
)
from .waker import waker_bp
from .sleeper import sleeper_bp


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application.
    
    This function creates a Flask application instance, loads configuration,
    registers error handlers, and sets up the API routes.
    
    Returns:
        Flask: The configured Flask application instance
        
    Configuration:
        The app loads configuration from 'config/sleep-manager-config.json'
        
    Routes:
        - GET /: Welcome message
        - GET /health: Health check endpoint
        - /sleeper/*: Sleeper-specific endpoints (see sleeper.py)
        - /waker/*: Waker-specific endpoints (see waker.py)
    """
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
        """Welcome endpoint.
        
        Returns a simple welcome message for the Sleep Manager API.
        
        **Authentication**: Not required
        
        **Response**:
            A plain text welcome message.
            
        **Example Response**:
            Welcome to sleep manager!
            
        **HTTP Status Codes**:
            - 200: Success
            
        **Example Usage**:
            .. code-block:: bash
                
                curl http://sleeper_url:51339/
        """
        return 'Welcome to sleep manager!'

    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint.
        
        This endpoint provides a comprehensive health status of the application
        and its components. It checks configuration validity and system command
        availability based on the role (sleeper or waker).
        
        **Authentication**: Not required
        
        **Response**:
            A JSON object containing health status information.
            
        **Response Format**:
            .. code-block:: json
            
                {
                    "status": "healthy",
                    "config": {
                        "valid": true,
                        "role": "sleeper",
                        "errors": []
                    },
                    "commands": {
                        "systemctl": {
                            "available": true,
                            "path": "/usr/bin/systemctl"
                        }
                    }
                }
                
        **HTTP Status Codes**:
            - 200: Success (healthy)
            - 500: Internal Server Error (unhealthy)
            
        **Example Usage**:
            .. code-block:: bash
                
                curl http://sleeper_url:51339/health
                
        **Example Response**:
            .. code-block:: json
            
                {
                    "status": "healthy",
                    "config": {
                        "valid": true,
                        "role": "sleeper",
                        "errors": []
                    },
                    "commands": {
                        "systemctl": {
                            "available": true,
                            "path": "/usr/bin/systemctl"
                        }
                    }
                }
        """
        try:
            # Check configuration
            config_errors = []
            role = None
            
            try:
                # Check if we have sleeper config
                if 'SLEEPER' in current_app.config:
                    role = 'sleeper'
                    required_keys = ['name', 'mac_address', 'suspend_exec']
                    for key in required_keys:
                        if key not in current_app.config['SLEEPER']:
                            config_errors.append(f"Missing SLEEPER.{key}")
                
                # Check if we have waker config
                if 'WAKER' in current_app.config:
                    if role is None:
                        role = 'waker'
                    required_keys = ['name', 'wol_exec']
                    for key in required_keys:
                        if key not in current_app.config['WAKER']:
                            config_errors.append(f"Missing WAKER.{key}")
                
                # Check API key
                if 'API_KEY' not in current_app.config:
                    config_errors.append("Missing API_KEY")
                    
            except Exception as e:
                config_errors.append(f"Configuration error: {str(e)}")
            
            # Check command availability based on role
            commands = {}
            if role == 'sleeper':
                commands['systemctl'] = check_command_availability('systemctl')
            elif role == 'waker':
                commands['etherwake'] = check_command_availability('etherwake')
            
            # Determine overall health
            config_valid = len(config_errors) == 0
            commands_healthy = all(cmd.get('available', False) for cmd in commands.values())
            overall_healthy = config_valid and commands_healthy
            
            return {
                'status': 'healthy' if overall_healthy else 'unhealthy',
                'config': {
                    'valid': config_valid,
                    'role': role,
                    'errors': config_errors
                },
                'commands': commands
            }
            
        except Exception as e:
            logger.exception("Health check failed")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }, 500

    return app
