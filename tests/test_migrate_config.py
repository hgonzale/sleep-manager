from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.migrate_config import migrate_config


def _load_toml(path: Path) -> dict[str, dict[str, object]]:
    import tomllib

    return tomllib.loads(path.read_text())


@pytest.mark.unit
class TestMigrateConfig:
    def test_migrate_basic_keys(self, tmp_path: Path) -> None:
        src = tmp_path / "config.json"
        dest = tmp_path / "config.toml"
        src.write_text(
            json.dumps(
                {
                    "DOMAIN": "localdomain",
                    "PORT": 51339,
                    "DEFAULT_REQUEST_TIMEOUT": 4,
                    "API_KEY": "secret",
                    "WAKER": {"name": "waker", "wol_exec": "/usr/sbin/etherwake"},
                    "SLEEPER": {"name": "sleeper", "mac_address": "aa:bb:cc"},
                }
            )
        )

        migrate_config(src, dest)
        data = _load_toml(dest)

        assert data["common"]["domain"] == "localdomain"
        assert data["common"]["port"] == 51339
        assert data["common"]["default_request_timeout"] == 4
        assert data["common"]["api_key"] == "secret"
        assert data["waker"]["name"] == "waker"
        assert data["waker"]["wol_exec"] == "/usr/sbin/etherwake"
        assert data["sleeper"]["name"] == "sleeper"
        assert data["sleeper"]["mac_address"] == "aa:bb:cc"

    def test_migrate_lowercase_common_keys(self, tmp_path: Path) -> None:
        src = tmp_path / "config.json"
        dest = tmp_path / "config.toml"
        src.write_text(
            json.dumps(
                {
                    "domain": "localdomain",
                    "port": 51339,
                    "default_request_timeout": 4,
                    "api_key": "secret",
                    "waker": {"name": "waker", "wol_exec": "/usr/sbin/etherwake"},
                    "sleeper": {"name": "sleeper", "mac": "aa:bb:cc"},
                }
            )
        )

        migrate_config(src, dest)
        data = _load_toml(dest)

        assert data["common"]["domain"] == "localdomain"
        assert data["common"]["port"] == 51339
        assert data["common"]["default_request_timeout"] == 4
        assert data["common"]["api_key"] == "secret"
        assert data["waker"]["name"] == "waker"
        assert data["sleeper"]["mac_address"] == "aa:bb:cc"

    def test_migrate_role_inference(self, tmp_path: Path) -> None:
        src = tmp_path / "config.json"
        dest = tmp_path / "config.toml"
        src.write_text(
            json.dumps(
                {
                    "API_KEY": "secret",
                    "WAKER": {"name": "waker", "wol_exec": "/usr/sbin/etherwake"},
                }
            )
        )

        migrate_config(src, dest)
        data = _load_toml(dest)

        assert "role" not in data["common"]

    def test_migrate_ambiguous_role(self, tmp_path: Path) -> None:
        src = tmp_path / "config.json"
        dest = tmp_path / "config.toml"
        src.write_text(
            json.dumps(
                {
                    "API_KEY": "secret",
                    "WAKER": {"name": "waker", "wol_exec": "/usr/sbin/etherwake"},
                    "SLEEPER": {"name": "sleeper", "mac_address": "aa:bb:cc"},
                }
            )
        )

        migrate_config(src, dest)
        data = _load_toml(dest)

        assert "role" not in data["common"]
