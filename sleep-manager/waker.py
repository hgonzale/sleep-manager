from flask import Blueprint, current_app
import requests
import subprocess
from typing import Any, Optional

from .sleeper import sleeper_url


waker_bp = Blueprint('waker', url_prefix='waker')


@waker_bp.get('/config')
def print_config() -> dict[str, Any]:
    return current_app.config


@waker_bp.get('/wake')
def wake() -> dict[str, Any]:
    sleeper_name = current_app.config['sleeper']['name']
    sleeper_mac = current_app.config['sleeper']['mac_address']
    wol_exec = current_app.config['waker']['wol_exec']

    # run wake command and get return_code
    _res = subprocess.run([wol_command, sleeper_mac], capture_output=True)

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


@waker_bp.get('/suspend')
def suspend():
    return sleeper_request('suspend')


@waker_bp.get('/status')
def status():
    return sleeper_request('status')


def waker_url() -> str:
    waker_name = current_app.config['waker']['name']
    domain = current_app.config['domain']
    port = current_app.config['port']

    return f'http://{waker_name}.{domain}:{port}/waker'


def sleeper_request(endpoint: str) -> dict[str, Any]:
    sleeper_url = sleeper_url()
    request_timeout = max(current_app.config['request_timeout'], 3.05) ## slightly larger than 3=TCP response window

    _res = requests.get(f'{sleeper_url}/{endpoint}', timeout=request_timeout)

    _timeout = False
    _json = {}
    match _res.status_code, _res.ok:
        case 408, _:
            _timeout = True
        case _, True:
            _json = _res.json
        case _code, False:
            abort(500, f'sleeper responded with code {_code}')

    return {
        'op': endpoint,
        'sleeper_response': {
            'status_code': _res.status_code,
            'json': _json,
            'text': _res.text,
            'url': _res.url,
        }
    }
