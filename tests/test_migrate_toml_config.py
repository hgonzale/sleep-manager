from __future__ import annotations

from pathlib import Path

import pytest

from scripts.migrate_toml_config import migrate_toml_config


def _load_toml(path: Path) -> dict[str, dict[str, object]]:
    import tomllib

    return tomllib.loads(path.read_text())


@pytest.mark.unit
class TestMigrateTomlConfig:
    def test_migrate_uppercase_sections(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sleep-manager-config.toml"
        config_path.write_text(
            """
[COMMON]
ROLE = "waker"
DOMAIN = "localdomain"
PORT = 51339
DEFAULT_REQUEST_TIMEOUT = 4
API_KEY = "secret"

[WAKER]
name = "waker"
wol_exec = "/usr/sbin/etherwake"

[SLEEPER]
name = "sleeper"
mac_address = "aa:bb:cc"
""".lstrip()
        )

        migrated = migrate_toml_config(config_path)
        assert migrated is True
        backups = list(tmp_path.glob("sleep-manager-config.toml.bak.*"))
        assert backups

        data = _load_toml(config_path)
        assert data["common"]["domain"] == "localdomain"
        assert data["common"]["port"] == 51339
        assert data["common"]["default_request_timeout"] == 4
        assert data["common"]["api_key"] == "secret"
        assert data["waker"]["name"] == "waker"
        assert data["sleeper"]["mac_address"] == "aa:bb:cc"

    def test_migrate_top_level_keys(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sleep-manager-config.toml"
        config_path.write_text(
            """
DOMAIN = "localdomain"
PORT = 51339
DEFAULT_REQUEST_TIMEOUT = 4
API_KEY = "secret"

[SLEEPER]
name = "sleeper"
mac = "aa:bb:cc"
""".lstrip()
        )

        migrated = migrate_toml_config(config_path)
        assert migrated is True
        data = _load_toml(config_path)
        assert data["common"]["api_key"] == "secret"
        assert data["sleeper"]["mac_address"] == "aa:bb:cc"

    def test_noop_for_lowercase_format(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sleep-manager-config.toml"
        content = """
[common]
domain = "localdomain"
port = 51339
default_request_timeout = 4
api_key = "secret"

[waker]
name = "waker"
wol_exec = "/usr/sbin/etherwake"
""".lstrip()
        config_path.write_text(content)

        migrated = migrate_toml_config(config_path)
        assert migrated is False
        backups = list(tmp_path.glob("sleep-manager-config.toml.bak.*"))
        assert not backups
        assert config_path.read_text() == content
