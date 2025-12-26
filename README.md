# Sleep Manager

Sleep Manager is a Flask app for managing sleep/wake cycles between two machines on the same LAN. A **waker** sends Wake-on-LAN packets, and a **sleeper** suspends itself on demand.
Both machines can use the same config content; the only difference should be `common.role` (`waker` or `sleeper`). Only the APIs for that role are exposed. Shared settings live under `[common]`; waker machines need `[waker]` plus the sleeper name/MAC in `[sleeper]`, and sleeper machines need `[sleeper]`.

## Requirements

- Python 3.11+
- Two Linux machines on the same local network
- systemd on both machines
- Wake-on-LAN capable NIC on the sleeper
- `etherwake` installed
- `ethtool` installed
- sudo access on both machines

## Install (Debian)

### Debian Package

```bash
sudo dpkg -i sleep-manager_*.deb
```

Download the latest `.deb` from GitHub Releases.

## Install (Other Linux Distros)

Follow the manual installation steps in the docs: `docs/installation.rst`.

## Key Configuration

Config file path (default): `/etc/sleep-manager/sleep-manager-config.toml`

Most important settings:

- `common.role`: required, either `waker` or `sleeper`
- `common.api_key`: shared secret for all authenticated endpoints
- `common.domain` and `common.port`: used to construct URLs for inter-machine calls
- `sleeper.name`: hostname used for sleeper API URLs (also required on the waker)
- `sleeper.mac_address`: MAC address used for Wake-on-LAN (required on the waker)
- `waker.name`: hostname used for waker API URLs
- `waker.wol_exec`: path to `etherwake`

See the example config in `config/sleep-manager-config.toml.example` (it includes comments about which sections each machine needs).

## Documentation

Full installation, configuration, operations, troubleshooting, and API docs are available at [https://hgonzale.github.io/sleep-manager/](https://hgonzale.github.io/sleep-manager/).

## HomeKit Integration

See `homebridge-sleep-manager/` for HomeKit integration using the
[`homebridge-http-switch` plugin](https://github.com/homebridge-plugins/homebridge-http-switch).

## License

BSD 2-clause License - see LICENSE file for details.
