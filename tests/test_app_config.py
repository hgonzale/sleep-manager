from __future__ import annotations

from pathlib import Path

import pytest

import sleep_manager.__init__ as sm_init
from sleep_manager.core import ConfigurationError


def test_normalize_section_uppercase_keys() -> None:
    data = {"COMMON": {"DOMAIN": "localdomain"}}
    result = sm_init._normalize_section(data, "common")
    assert result["domain"] == "localdomain"


def test_normalize_section_non_table() -> None:
    data = {"COMMON": "nope"}
    with pytest.raises(ConfigurationError, match="common config section must be a table"):
        sm_init._normalize_section(data, "common")


def test_resolve_role_matches_sleeper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sm_init.socket, "gethostname", lambda: "sleeper-host")
    monkeypatch.setattr(sm_init.socket, "getfqdn", lambda: "sleeper-host.localdomain")

    role = sm_init._resolve_role(
        {"domain": "localdomain", "api_key": "test"},
        {"name": "waker-host"},
        {"name": "sleeper-host"},
    )

    assert role == "sleeper"


def test_resolve_config_path_env_missing_uses_example(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    example_path = tmp_path / "example.toml"
    example_path.write_text("[common]\napi_key = \"test\"\n")
    monkeypatch.setenv(sm_init.CONFIG_ENV_VAR, str(tmp_path / "missing.toml"))
    monkeypatch.setattr(sm_init, "EXAMPLE_CONFIG_PATH", example_path)

    resolved = sm_init._resolve_config_path()
    assert resolved == example_path


def test_resolve_config_path_missing_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(sm_init.CONFIG_ENV_VAR, str(tmp_path / "missing.toml"))
    monkeypatch.setattr(sm_init, "EXAMPLE_CONFIG_PATH", tmp_path / "also-missing.toml")

    with pytest.raises(FileNotFoundError):
        sm_init._resolve_config_path()


def test_role_candidates_with_domain() -> None:
    assert sm_init._role_candidates("waker-host", "localdomain") == {
        "waker-host",
        "waker-host.localdomain",
    }


def test_role_candidates_without_name() -> None:
    assert sm_init._role_candidates(None, "localdomain") == set()
