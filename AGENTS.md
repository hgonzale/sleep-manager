# Sleep Manager Agent Notes

## Project overview

Two-machine sleep/wake control over HTTP on a trusted LAN. One machine is the **waker** (always on), the other is the **sleeper** (can be suspended). Both run the same Flask app; only one blueprint (`waker_bp` or `sleeper_bp`) is registered per process, determined at startup by role resolution.

## Role resolution

Role is determined by matching the current hostname (and FQDN) against `[waker].name` / `[sleeper].name` in the config. A `ConfigurationError` is raised if the hostname matches neither or both. See `__init__.py:_resolve_role`.

## Configuration

- **Format:** TOML, loaded with `tomllib`
- **Path resolution:** `SLEEP_MANAGER_CONFIG_PATH` env var → `/etc/sleep-manager/sleep-manager-config.toml` → repo example fallback
- **Sections:** `[common]`, `[waker]`, `[sleeper]` (keys are lowercased at load time)
- **Required common key:** `api_key`
- **Optional common keys (have defaults):** `heartbeat_interval` (60s), `wake_timeout` (120s), `heartbeat_miss_threshold` (3)
- Both machines can share the same config file; role is resolved from the hostname at runtime.

## State machine (waker role only)

`SleeperStateMachine` (`sleep_manager/state_machine.py`) tracks sleeper reachability on the waker:

- States: `OFF → WAKING → ON`, `FAILED` if wake times out
- Transitions: `wake_requested()`, `heartbeat_received()`, `suspend_requested()`, `check_timeouts()`
- `check_timeouts()` is called every 10s by a daemon thread started in `create_app()`
- Stored at `app.extensions["state_machine"]`
- `_time_fn` is injectable for testing (pass `lambda: clock[0]` with a mutable list)

## Heartbeat protocol

The sleeper POSTs to `POST /waker/heartbeat` every `heartbeat_interval` seconds via a background thread started by `_start_heartbeat_sender(app)`. After `suspend_requested()`, the waker suppresses incoming heartbeats for `2 × heartbeat_interval` to prevent bounce-back to ON state.

## Authentication

All operational endpoints require `X-API-Key` matching `common.api_key`. Only `GET /` and `GET /health` are unauthenticated.

## Logging safety

- Never log `api_key`, `X-API-Key` header, or full request headers.
- Redact MAC addresses if they appear in log output.
- Do not log full config contents or raw exception messages that could reveal secrets or paths.
- Return generic error messages to clients; log detail server-side only.

## Testing

- Tests use the `make_config` fixture (`tests/conftest.py`), which writes a temp TOML and sets `SLEEP_MANAGER_CONFIG_PATH`. Any new config keys must be added to the template inside `_write_config`.
- `app.extensions["state_machine"]` is accessible in tests for state inspection/manipulation.
- Unit tests: `@pytest.mark.unit` in `test_sleeper.py`, `test_waker.py`, and others.
- Integration tests: `@pytest.mark.integration` in `test_integration.py`.
- Run all: `uv run tox -e test` | unit only: `uv run pytest -m unit`
- After changing dependencies in `pyproject.toml`, regenerate `uv.lock` and `requirements.txt` with `uv run tox -e deps` (do not run `uv lock` directly)
- Coverage threshold: 85%

## Commit messages and release notes

Short and factual. One to two sentences per change. No filler or marketing language.

## Tooling

- Python 3.11+, uv
- Lint: Ruff (`tox -e lint`)
- Type check: Ty (`tox -e typecheck`)
- Docs: Sphinx (`tox -e docs`)
