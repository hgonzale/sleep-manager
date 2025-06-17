from flask import Blueprint, current_app
import requests
import subprocess
from typing import Any
import logging
from . import require_api_key, ConfigurationError, SystemCommandError

logger = logging.getLogger(__name__)

sleeper_bp = Blueprint('sleeper', __name__, url_prefix='/sleeper')


@sleeper_bp.get('/config')
@require_api_key
def print_config() -> dict[str, Any]:
    return current_app.config


@sleeper_bp.get('/suspend')
@require_api_key
def suspend() -> dict[str, Any]:
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
    try:
        sleeper_name = current_app.config['SLEEPER']['name']
        domain = current_app.config['DOMAIN']
        port = current_app.config['PORT']

        return f'http://{sleeper_name}.{domain}:{port}/sleeper'
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")
