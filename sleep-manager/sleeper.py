from flask import Blueprint, current_app
import requests
import subprocess
from typing import Any


sleeper_bp = Blueprint('sleeper', url_prefix='sleeper')


@sleeper_bp.get('/config')
def print_config() -> dict[str, Any]:
    return current_app.config


@sleeper_bp.get('/suspend')
def suspend() -> dict[str, Any]:
    systemctl_exec = current_app.config['sleeper']['systemctl_command']
    suspend_verb = current_app.config['sleeper']['suspend_verb']

    # Once this command is executed, we have a race between the system suspend
    # and Flask responding the request. We assume that systemd-sleep has been
    # added a pre-suspend service with a delay of ~5 secs, so this Flask has
    # enough time to respond.
    _res = subprocess.Popen([systemctl_exec, suspend_verb])

    return {
        'op': 'suspend',
        'subprocess': {
            'args': [systemctl_exec, suspend_verb],
        }
    }

@sleeper_bp.get('/status')
def status():
    systemctl_exec = current_app.config['sleeper']['systemctl_command']
    status_verb = current_app.config['sleeper']['status_verb']

    # run systemd status command
    _res = subprocess.run([systemctl_exec, status_verb], capture_output=True)

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


def sleeper_url() -> str:
    sleeper_name = current_app.config['sleeper']['name']
    domain = current_app.config['domain']
    port = current_app.config['port']

    return f'http://{sleeper_name}.{domain}:{port}/sleeper'
