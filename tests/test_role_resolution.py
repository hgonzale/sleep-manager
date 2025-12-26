from __future__ import annotations

import pytest

import sleep_manager.__init__ as sm_init
from sleep_manager.core import ConfigurationError


def _common(domain: str = "localdomain") -> dict[str, str]:
    return {"domain": domain, "api_key": "test"}


def test_resolve_role_matches_waker_short(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sm_init.socket, "gethostname", lambda: "waker-host")
    monkeypatch.setattr(sm_init.socket, "getfqdn", lambda: "waker-host.localdomain")

    role = sm_init._resolve_role(
        _common(),
        {"name": "waker-host"},
        {"name": "sleeper-host"},
    )

    assert role == "waker"


def test_resolve_role_matches_waker_fqdn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sm_init.socket, "gethostname", lambda: "unrelated")
    monkeypatch.setattr(sm_init.socket, "getfqdn", lambda: "waker-host.localdomain")

    role = sm_init._resolve_role(
        _common(),
        {"name": "waker-host"},
        {"name": "sleeper-host"},
    )

    assert role == "waker"


def test_resolve_role_ambiguous(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sm_init.socket, "gethostname", lambda: "shared-host")
    monkeypatch.setattr(sm_init.socket, "getfqdn", lambda: "shared-host.localdomain")

    with pytest.raises(ConfigurationError, match="Hostname matches both waker and sleeper"):
        sm_init._resolve_role(
            _common(),
            {"name": "shared-host"},
            {"name": "shared-host"},
        )


def test_resolve_role_no_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sm_init.socket, "gethostname", lambda: "unknown-host")
    monkeypatch.setattr(sm_init.socket, "getfqdn", lambda: "unknown-host.localdomain")

    with pytest.raises(ConfigurationError, match="Hostname did not match waker or sleeper"):
        sm_init._resolve_role(
            _common(),
            {"name": "waker-host"},
            {"name": "sleeper-host"},
        )
