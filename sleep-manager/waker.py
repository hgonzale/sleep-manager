from flask import Blueprint, current_app
import json
import requests
import subprocess
from typing import Any, Optional
import logging
from . import require_api_key, ConfigurationError, SystemCommandError, NetworkError
from .sleeper import sleeper_url

logger = logging.getLogger(__name__)

waker_bp = Blueprint('waker', __name__, url_prefix='/waker')


@waker_bp.get('/config')
@require_api_key
def print_config() -> dict[str, Any]:
    return current_app.config['WAKER']


@waker_bp.get('/wake')
@require_api_key
def wake() -> dict[str, Any]:
    try:
        sleeper_name = current_app.config['SLEEPER']['name']
        sleeper_mac = current_app.config['SLEEPER']['mac_address']
        wol_exec = current_app.config['WAKER']['wol_exec']

        logger.info(f"Attempting to wake {sleeper_name} using {wol_exec} {sleeper_mac}")

        # run wake command and get return_code
        _res = subprocess.run([wol_exec, sleeper_mac], capture_output=True, text=True)

        if _res.returncode != 0:
            raise SystemCommandError(
                "Wake command failed",
                command=f"{wol_exec} {sleeper_mac}",
                return_code=_res.returncode,
                stderr=_res.stderr
            )

        logger.info(f"Successfully sent wake command to {sleeper_name}")
        return {
            'op': 'wake',
            'sleeper': {
                'name': sleeper_name,
                'mac_address': sleeper_mac,
            },
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
        logger.exception("Failed to wake sleeper")
        raise SystemCommandError(
            "Failed to wake sleeper",
            command=f"{wol_exec} {sleeper_mac}",
            return_code=-1,
            stderr=str(e)
        )


@waker_bp.get('/suspend')
@require_api_key
def suspend() -> dict[str, Any]:
    return sleeper_request('suspend')


@waker_bp.get('/status')
@require_api_key
def status() -> dict[str, Any]:
    return sleeper_request('status')


def waker_url() -> str:
    try:
        waker_name = current_app.config['WAKER']['name']
        domain = current_app.config['DOMAIN']
        port = current_app.config['PORT']

        return f'http://{waker_name}.{domain}:{port}/waker'
    except KeyError as e:
        raise ConfigurationError(f"Missing configuration: {str(e)}")


def sleeper_request(endpoint: str) -> dict[str, Any]:
    try:
        url = sleeper_url()
        request_timeout = max(current_app.config['DEFAULT_REQUEST_TIMEOUT'], 3.05)  # slightly larger than 3=TCP response window

        logger.info(f"Making request to sleeper at {url}/{endpoint}")

        _res = requests.get(
            f'{url}/{endpoint}',
            timeout=request_timeout,
            headers={'X-API-Key': current_app.config['API_KEY']}
        )

        _timeout = False
        _json = {}
        
        # Handle response status
        if _res.status_code == 408:
            _timeout = True
            raise NetworkError("Request to sleeper timed out")
        elif not _res.ok:
            raise NetworkError(
                f"Sleeper responded with error code {_res.status_code}",
                details={'response': _res.text}
            )
        else:
            _json = _res.json()

        logger.info(f"Successfully received response from sleeper for {endpoint}")
        return {
            'op': endpoint,
            'sleeper_response': {
                'status_code': _res.status_code,
                'json': _json,
                'text': _res.text,
                'url': _res.url,
            }
        }
    except requests.exceptions.Timeout:
        logger.error("Request to sleeper timed out")
        raise NetworkError("Request to sleeper timed out")
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to communicate with sleeper")
        raise NetworkError(f"Failed to communicate with sleeper: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error during sleeper request")
        raise NetworkError(f"Unexpected error: {str(e)}")
