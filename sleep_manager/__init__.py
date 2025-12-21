import logging
import os
from pathlib import Path
from typing import Any, cast

from flask import Flask, current_app, json

from .core import SleepManagerError, check_command_availability, handle_error
from .sleeper import sleeper_bp
from .waker import waker_bp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


CONFIG_ENV_VAR = "SLEEP_MANAGER_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path("/etc/sleep-manager/sleep-manager-config.json")
EXAMPLE_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "sleep-manager-config.json.example"
)


def _resolve_config_path() -> Path:
    env_path = os.environ.get(CONFIG_ENV_VAR)
    config_path = Path(env_path) if env_path else DEFAULT_CONFIG_PATH
    if config_path.exists():
        return config_path
    if EXAMPLE_CONFIG_PATH.exists():
        logger.warning(
            "Config file %s not found; falling back to example config %s",
            config_path,
            EXAMPLE_CONFIG_PATH,
        )
        return EXAMPLE_CONFIG_PATH
    raise FileNotFoundError(
        f"Configuration file not found at {config_path!s}; "
        f"set {CONFIG_ENV_VAR} to a valid config path"
    )


def create_app() -> Flask:
    """Create and configure the Flask application.

    This function creates a Flask application instance, loads configuration,
    registers error handlers, and sets up the API routes.

    Returns:
        Flask: The configured Flask application instance

    Configuration:
        The app loads configuration from the path defined in
        `SLEEP_MANAGER_CONFIG_PATH`, defaults to
        `/etc/sleep-manager/sleep-manager-config.json`, and falls
        back to `config/sleep-manager-config.json.example` inside the repository.

    Routes:
        - GET /: Welcome message
        - GET /health: Health check endpoint
        - /sleeper/*: Sleeper-specific endpoints (see sleeper.py)
        - /waker/*: Waker-specific endpoints (see waker.py)
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    config_path = _resolve_config_path()
    app.config.from_file(config_path, load=json.load, text=True)
    logger.info(f"Loaded config: {app.config.get('SLEEPER')}")

    # Register error handlers
    app.register_error_handler(SleepManagerError, handle_error)
    app.register_error_handler(Exception, handle_error)

    # Register blueprints with authentication
    app.register_blueprint(waker_bp)
    app.register_blueprint(sleeper_bp)

    @app.route("/")
    def welcome() -> str:
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
        return "Welcome to sleep manager!"

    @app.route("/health")
    def health_check() -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Comprehensive health check endpoint."""

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
            return obj

        try:
            # Check configuration
            config_errors = []
            role = None

            try:
                # Check if we have sleeper config
                if "SLEEPER" in current_app.config:
                    role = "sleeper"
                    required_keys = ["name", "mac_address", "suspend_verb"]
                    for key in required_keys:
                        if key not in current_app.config["SLEEPER"]:
                            config_errors.append(f"Missing SLEEPER.{key}")

                # Check if we have waker config
                if "WAKER" in current_app.config:
                    if role is None:
                        role = "waker"
                    required_keys = ["name", "wol_exec"]
                    for key in required_keys:
                        if key not in current_app.config["WAKER"]:
                            config_errors.append(f"Missing WAKER.{key}")

                # Check API key
                if "API_KEY" not in current_app.config:
                    config_errors.append("Missing API_KEY")

            except Exception as e:
                config_errors.append(f"Configuration error: {str(e)}")

            # Check command availability based on role
            commands: dict[str, dict[str, Any]] = {}
            if role == "sleeper":
                commands["systemctl"] = check_command_availability("systemctl")
            elif role == "waker":
                commands["etherwake"] = check_command_availability("etherwake")

            # Determine overall health
            config_valid = len(config_errors) == 0
            commands_healthy = all(cmd.get("available", False) for cmd in commands.values())
            overall_healthy = config_valid and commands_healthy

            result: dict[str, Any] = {
                "status": "healthy" if overall_healthy else "unhealthy",
                "config": {
                    "valid": config_valid,
                    "role": role,
                    "errors": config_errors,
                },
                "commands": commands,
            }
            return cast(dict[str, Any], sanitize(result))

        except Exception as e:
            logger.exception("Health check failed")
            return {"status": "unhealthy", "error": "Health check failed"}, 500

    return app
