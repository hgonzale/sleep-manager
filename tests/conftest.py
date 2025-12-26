from __future__ import annotations

import socket
from pathlib import Path

import pytest


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
