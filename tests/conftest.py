from __future__ import annotations

import socket
from pathlib import Path

import pytest

from sleep_manager.state_machine import SleeperStateMachine


def _write_config(path: Path, role: str) -> None:
    hostname = socket.gethostname()
    waker_name = hostname if role == "waker" else "test-waker"
    sleeper_name = hostname if role == "sleeper" else "test-sleeper"
    content = f"""
[common]
domain = "test.local"
port = 5000
default_request_timeout = 3
api_key = "test-api-key"
heartbeat_interval = 60
wake_timeout = 120
heartbeat_miss_threshold = 3

[waker]
name = "{waker_name}"
wol_exec = "/usr/sbin/etherwake"

[sleeper]
name = "{sleeper_name}"
mac_address = "00:11:22:33:44:55"
systemctl_command = "/usr/bin/systemctl"
suspend_verb = "suspend"
status_verb = "is-system-running"
""".lstrip()
    path.write_text(content)


@pytest.fixture
def make_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def _make(role: str) -> Path:
        config_path = tmp_path / f"sleep-manager-{role}.toml"
        _write_config(config_path, role)
        monkeypatch.setenv("SLEEP_MANAGER_CONFIG_PATH", str(config_path))
        return config_path

    return _make


@pytest.fixture
def state_machine():
    """Pre-built SleeperStateMachine with a mocked time function."""
    clock = [1_000_000.0]
    sm = SleeperStateMachine(
        wake_timeout=120.0,
        heartbeat_interval=60.0,
        heartbeat_miss_threshold=3,
        _time_fn=lambda: clock[0],
    )
    sm._clock = clock  # expose clock for tests that need to advance time
    return sm
