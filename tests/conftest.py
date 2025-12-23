from __future__ import annotations

from pathlib import Path

import pytest


def _write_config(path: Path, role: str) -> None:
    content = f"""
[COMMON]
ROLE = "{role}"
DOMAIN = "test.local"
PORT = 5000
DEFAULT_REQUEST_TIMEOUT = 3
API_KEY = "test-api-key"

[WAKER]
name = "test-waker"
wol_exec = "/usr/sbin/etherwake"

[SLEEPER]
name = "test-sleeper"
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
