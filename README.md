# Sleep Manager

A Flask-based application for managing sleep/wake cycles between two machines on a local network. The system consists of a "sleeper" machine that can be suspended and woken remotely, and a "waker" machine that sends Wake-on-LAN packets to wake the sleeper.

## Quick Start

1. **Clone and setup**:

   ```bash
   git clone <repository-url>
   cd sleep-manager
   chmod +x scripts/setup-system.sh
   ```

2. **Setup machines**:

   ```bash
   # Setup sleeper (machine that will be suspended)
   sudo ./scripts/setup-system.sh sleeper
   
   # Setup waker (machine that will wake the sleeper)
   sudo ./scripts/setup-system.sh waker
   ```

3. **Configure**:

   ```bash
   sudo mkdir -p /usr/local/sleep-manager/config
   sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json
   ```

4. **Start services**:

   ```bash
   sudo systemctl start sleep-manager-sleeper
   sudo systemctl start sleep-manager-waker
   sudo systemctl enable sleep-manager-sleeper
   sudo systemctl enable sleep-manager-waker
   ```

## Architecture

```text
[Waker Machine] ---- [Local Network] ---- [Sleeper Machine]
    (waker_url)                              (sleeper_url)
```

- **Sleeper**: Runs Flask app on port 51339, can be suspended via API
- **Waker**: Runs Flask app on port 51339, sends Wake-on-LAN packets
- **Communication**: HTTP API with API key authentication

## Configuration Example

```json
{
    "WAKER": {
        "name": "waker_url",
        "ip": "192.168.1.100",
        "mac": "00:11:22:33:44:55"
    },
    "SLEEPER": {
        "name": "sleeper_url",
        "ip": "192.168.1.101",
        "mac": "AA:BB:CC:DD:EE:FF"
    },
    "API_KEY": "your-secure-api-key-here"
}
```

## Quick Test

```bash
# Test wake
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

# Test suspend
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

# Check status
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
```

## Documentation

- [Deployment Guide](DEPLOYMENT.md) - Detailed setup instructions
- [System Requirements](SYSTEM_REQUIREMENTS.md) - Requirements and compatibility
- [Quick Reference](QUICK_REFERENCE.md) - Common commands
- [API Documentation](docs/_build/html/index.html) - Complete API reference (build with `./scripts/build-docs.sh build`)

## Development Environment

The repository uses [uv](https://github.com/astral-sh/uv) for dependency management, [tox](https://tox.wiki/) for task automation, [Ruff](https://docs.astral.sh/ruff/) for formatting/linting, and [mypy](https://mypy-lang.org/) for static typing. After installing `uv`, run:

```bash
uv sync --group dev
```

> **Note:** The `uv sync` run provisions the repo-local `.venv`; activate it or run commands directly from `./.venv/bin/...` so you always execute tools against that synced environment (e.g., `./.venv/bin/mypy`).

Common development tasks:

```bash
# Run the default test matrix
uv run tox

# Target specific environments
uv run tox -e py311         # Unit tests on Python 3.11
uv run tox -e lint          # Ruff lint checks
uv run tox -e typecheck     # mypy

# Format and lint quickly
uv run ruff format .
uv run ruff check .
```

## HomeKit Integration

See [homebridge-sleep-manager/](homebridge-sleep-manager/) for HomeKit integration using the `homebridge-http-switch` plugin.

## License

BSD 2-clause License - see LICENSE file for details.
