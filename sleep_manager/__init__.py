import logging
import os
import socket
import tomllib
from pathlib import Path
from typing import Any, cast

from flask import Flask, current_app

from .core import ConfigurationError, SleepManagerError, check_command_availability, handle_error
from .sleeper import sleeper_bp
from .waker import waker_bp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


CONFIG_ENV_VAR = "SLEEP_MANAGER_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path("/etc/sleep-manager/sleep-manager-config.toml")
EXAMPLE_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "sleep-manager-config.toml.example"
)


def _lowercase_keys(data: dict[str, Any]) -> dict[str, Any]:
    return {str(key).lower(): value for key, value in data.items()}


def _normalize_section(config_data: dict[str, Any], section: str) -> dict[str, Any]:
    section_value = config_data.get(section)
    if section_value is None:
        section_value = config_data.get(section.upper())
    if section_value is None:
        return {}
    if not isinstance(section_value, dict):
        raise ConfigurationError(f"{section} config section must be a table")
    return _lowercase_keys(section_value)


def _hostname_identifiers() -> tuple[set[str], str, str]:
    hostname = socket.gethostname()
    fqdn = socket.getfqdn()
    identifiers = {hostname.lower(), fqdn.lower()}
    for value in list(identifiers):
        if "." in value:
            identifiers.add(value.split(".", 1)[0])
    return identifiers, hostname, fqdn


def _role_candidates(name: str | None, domain: str | None) -> set[str]:
    candidates: set[str] = set()
    if name:
        candidates.add(name.lower())
        if domain:
            candidates.add(f"{name}.{domain}".lower())
    return candidates


def _resolve_role(common: dict[str, Any], waker: dict[str, Any], sleeper: dict[str, Any]) -> str:
    identifiers, hostname, fqdn = _hostname_identifiers()
    domain = common.get("domain")
    waker_candidates = _role_candidates(waker.get("name"), domain)
    sleeper_candidates = _role_candidates(sleeper.get("name"), domain)

    matches: dict[str, set[str]] = {}
    if identifiers & waker_candidates:
        matches["waker"] = identifiers & waker_candidates
    if identifiers & sleeper_candidates:
        matches["sleeper"] = identifiers & sleeper_candidates

    if len(matches) == 1:
        return next(iter(matches.keys()))
    if len(matches) > 1:
        raise ConfigurationError(
            "Hostname matches both waker and sleeper. "
            f"hostname={hostname!s}, fqdn={fqdn!s}, "
            f"waker_candidates={sorted(waker_candidates)!s}, "
            f"sleeper_candidates={sorted(sleeper_candidates)!s}"
        )
    raise ConfigurationError(
        "Hostname did not match waker or sleeper names. "
        f"hostname={hostname!s}, fqdn={fqdn!s}, "
        f"waker_candidates={sorted(waker_candidates)!s}, "
        f"sleeper_candidates={sorted(sleeper_candidates)!s}"
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
        `/etc/sleep-manager/sleep-manager-config.toml`, and falls
        back to `config/sleep-manager-config.toml.example` inside the repository.
        Shared settings live under the `common` section.

    Routes:
        - GET /: Welcome message
        - GET /health: Health check endpoint
        - /sleeper/*: Sleeper-specific endpoints (see sleeper.py)
        - /waker/*: Waker-specific endpoints (see waker.py)
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    config_path = _resolve_config_path()
    with config_path.open("rb") as config_file:
        config_data = tomllib.load(config_file)
    common_config = _normalize_section(config_data, "common")
    waker_config = _normalize_section(config_data, "waker")
    sleeper_config = _normalize_section(config_data, "sleeper")
    app.config.from_mapping(
        {
            "COMMON": common_config,
            "WAKER": waker_config,
            "SLEEPER": sleeper_config,
        }
    )

    role = _resolve_role(common_config, waker_config, sleeper_config)
    logger.info("Loaded config for role=%s", role)

    # Register error handlers
    app.register_error_handler(SleepManagerError, handle_error)
    app.register_error_handler(Exception, handle_error)

    # Register role-specific blueprints with authentication
    if role == "waker":
        app.register_blueprint(waker_bp)
    else:
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
                common = current_app.config.get("COMMON", {})
                waker = current_app.config.get("WAKER", {})
                sleeper = current_app.config.get("SLEEPER", {})
                role = _resolve_role(common, waker, sleeper)

                if role == "waker":
                    required_waker = ["name", "wol_exec"]
                    for key in required_waker:
                        if key not in waker:
                            config_errors.append(f"Missing waker.{key}")
                    if not sleeper:
                        config_errors.append("Missing sleeper")
                    else:
                        required_sleeper = ["name", "mac_address"]
                        for key in required_sleeper:
                            if key not in sleeper:
                                config_errors.append(f"Missing sleeper.{key}")
                elif role == "sleeper":
                    required_sleeper = [
                        "systemctl_command",
                        "suspend_verb",
                        "status_verb",
                    ]
                    for key in required_sleeper:
                        if key not in sleeper:
                            config_errors.append(f"Missing sleeper.{key}")
                if "api_key" not in common:
                    config_errors.append("Missing common.api_key")

            except Exception:
                logger.exception("Configuration error during health check")
                config_errors.append("Configuration error")

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

        except Exception:
            logger.exception("Health check failed")
            return {"status": "unhealthy", "error": "Health check failed"}, 500

    return app
