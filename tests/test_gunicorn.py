"""Gunicorn smoke tests: startup, HTTP, log format, clean shutdown."""
from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.gunicorn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(path: Path, role: str) -> None:
    hostname = socket.gethostname()
    waker_name = hostname if role == "waker" else "test-waker"
    sleeper_name = hostname if role == "sleeper" else "test-sleeper"
    path.write_text(
        f"""[common]
domain = "test.local"
port = 51339
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
"""
    )


class _UnixHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection that speaks over a unix socket."""

    def __init__(self, sock_path: str) -> None:
        super().__init__("localhost")
        self._sock_path = sock_path

    def connect(self) -> None:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._sock_path)
        self.sock = s


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def gunicorn_server(tmp_path: Path):
    """
    Yields a callable start(role) -> (sock_path, proc, log_path).
    Cleans up any started processes on teardown.
    """
    started: list[tuple[subprocess.Popen, object]] = []
    # AF_UNIX path limit is 104 chars on macOS, 108 on Linux.
    # pytest's tmp_path under macOS exceeds this, so use a short dir under /tmp.
    sock_dir = Path(tempfile.mkdtemp(prefix="sm-", dir="/tmp"))
    sock_dirs = [sock_dir]

    def _start(role: str) -> tuple[str, subprocess.Popen, Path]:
        config_path = tmp_path / f"config-{role}.toml"
        _write_config(config_path, role)
        sock_path = str(sock_dir / f"{role}.sock")
        log_path = tmp_path / f"{role}.log"

        env = os.environ.copy()
        env["SLEEP_MANAGER_CONFIG_PATH"] = str(config_path)
        # Don't bleed coverage instrumentation into the subprocess
        for key in ("COV_CORE_SOURCE", "COV_CORE_CONFIG", "COV_CORE_DATAFILE"):
            env.pop(key, None)

        log_fh = log_path.open("w")
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "gunicorn",
                "--bind", f"unix:{sock_path}",
                "--workers", "1",
                "--timeout", "5",
                "sleep_manager:create_app()",
            ],
            env=env,
            stdout=log_fh,
            stderr=log_fh,
        )
        started.append((proc, log_fh))

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if os.path.exists(sock_path):
                break
            rc = proc.poll()
            if rc is not None:
                log_fh.flush()
                pytest.fail(f"gunicorn exited with code {rc}:\n{log_path.read_text()}")
            time.sleep(0.05)
        else:
            proc.kill()
            proc.wait()
            log_fh.flush()
            pytest.fail(f"gunicorn socket never appeared:\n{log_path.read_text()}")

        return sock_path, proc, log_path

    yield _start

    for proc, log_fh in started:
        log_fh.flush()  # type: ignore[attr-defined]
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        log_fh.close()  # type: ignore[attr-defined]
    for d in sock_dirs:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["waker", "sleeper"])
def test_health_returns_200(gunicorn_server, role):
    sock_path, _, _ = gunicorn_server(role)
    conn = _UnixHTTPConnection(sock_path)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    assert resp.status == 200
    body = json.loads(resp.read())
    assert body["config"]["role"] == role


@pytest.mark.parametrize("role", ["waker", "sleeper"])
def test_log_format_no_timestamp(gunicorn_server, role):
    sock_path, proc, log_path = gunicorn_server(role)
    conn = _UnixHTTPConnection(sock_path)
    conn.request("GET", "/health")
    conn.getresponse().read()

    proc.terminate()
    proc.wait(timeout=5)

    log_text = log_path.read_text()
    app_lines = [
        line for line in log_text.splitlines()
        if "sleep_manager" in line and "INFO" in line
    ]
    assert app_lines, f"No app log lines found in:\n{log_text}"

    timestamp_re = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
    for line in app_lines:
        assert not timestamp_re.search(line), f"Timestamp in app log line: {line!r}"


@pytest.mark.parametrize("role", ["waker", "sleeper"])
def test_clean_shutdown(gunicorn_server, role):
    """SIGTERM must cause a clean exit within 5 seconds."""
    sock_path, proc, _ = gunicorn_server(role)
    conn = _UnixHTTPConnection(sock_path)
    conn.request("GET", "/health")
    assert conn.getresponse().status == 200

    proc.terminate()
    try:
        rc = proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        pytest.fail("gunicorn did not shut down within 5s of SIGTERM")
    assert rc == 0, f"gunicorn exited with code {rc}"
