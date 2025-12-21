# Sleep Manager Agent Notes

## Project snapshot

- **Purpose:** Two-machine sleep/wake control over HTTP on a trusted LAN (sleeper + waker).
- **Runtime:** Flask app with two blueprints (`/sleeper/*` and `/waker/*`) plus `"/"` and `"/health"` endpoints.
- **System integration:** Sleeper invokes `systemctl` for suspend/status; waker invokes `etherwake` for WoL.

## Design decisions (why things are shaped this way)

- **Single service, role-based behavior:** Both roles share one Flask app and config; which role is active is inferred from config keys. This keeps deployment symmetric across machines.
- **Explicit API key gate:** All operational endpoints require `X-API-Key` via a shared decorator; only `"/"` and `"/health"` are unauthenticated for diagnostics.
- **Config-driven runtime:** Config is loaded from `SLEEP_MANAGER_CONFIG_PATH` when set, otherwise `/usr/local/sleep-manager/config/sleep-manager-config.json`, with a repo example fallback to help local dev.
- **System safety:** Suspend is triggered via `systemctl` with a short race-aware delay (handled by systemd pre-suspend service configured by scripts), keeping the HTTP response reliable.
- **Network resilience:** Waker-to-sleeper calls wrap `requests.get` with timeouts and structured error responses to handle sleep/offline states cleanly.
- **Central error handling:** Custom error classes with a shared Flask error handler return consistent JSON error payloads.

## Configuration essentials

- **Keys:** `SLEEPER`, `WAKER`, `API_KEY`, `DOMAIN`, `PORT`, `DEFAULT_REQUEST_TIMEOUT`.
- **Default port:** 51339 (documented in the README/quick reference).

## Testing segmentation

- **Unit tests:** Marked with `@pytest.mark.unit` in `tests/test_sleeper.py` and `tests/test_waker.py`. These mock subprocess/network calls.
- **Integration tests:** Marked with `@pytest.mark.integration` in `tests/test_integration.py`. These exercise full Flask flows with mocked system/network boundaries.
- **How to run:**
  - `uv run tox -e test` (runs the full test suite)
  - `uv run pytest -m unit`
  - `uv run pytest -m integration`

## Tooling expectations

- **Python:** 3.11+
- **Lint:** Ruff
- **Type check:** Ty
- **Docs:** Sphinx via `tox -e docs`
