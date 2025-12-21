# Sleep Manager

Sleep Manager is a Flask app for managing sleep/wake cycles between two machines on the same LAN. A **waker** sends Wake-on-LAN packets, and a **sleeper** suspends itself on demand.

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
./scripts/build-deb.sh
sudo dpkg -i dist/deb/sleep-manager_*.deb
```

## Install (Other Linux Distros)

Follow the manual installation steps in the docs: `docs/installation.rst`.

## Key Configuration

Config file path (default): `/etc/sleep-manager/sleep-manager-config.json`

Most important settings:

- `API_KEY`: shared secret for all authenticated endpoints
- `SLEEPER.name`: hostname used for sleeper API URLs
- `SLEEPER.mac_address`: MAC address used for Wake-on-LAN
- `WAKER.name`: hostname used for waker API URLs
- `WAKER.wol_exec`: path to `etherwake`
- `DOMAIN` and `PORT`: used to construct URLs for inter-machine calls

See the example config in `config/sleep-manager-config.json.example`.

## Documentation

Full installation, configuration, operations, troubleshooting, and API docs are available at [https://hgonzale.github.io/sleep-manager/](https://hgonzale.github.io/sleep-manager/).

## HomeKit Integration

See `homebridge-sleep-manager/` for HomeKit integration using the
[`homebridge-http-switch` plugin](https://github.com/homebridge-plugins/homebridge-http-switch).

## License

BSD 2-clause License - see LICENSE file for details.
