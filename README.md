# Sleep Manager

Sleep Manager is a Flask app for managing sleep/wake cycles between two machines on the same LAN. A **waker** sends Wake-on-LAN packets, and a **sleeper** suspends itself on demand.

## Requirements

- Python 3.11+
- Two Linux machines on the same local network
- systemd on both machines
- Wake-on-LAN capable NIC on the sleeper
- `etherwake` installed on the waker
- sudo access on both machines

## Install

```bash
git clone <repository-url>
cd sleep-manager
chmod +x scripts/setup-system.sh

# Sleeper machine
sudo ./scripts/setup-system.sh sleeper

# Waker machine
sudo ./scripts/setup-system.sh waker
```

## Key Configuration

Config file path (default): `/usr/local/sleep-manager/config/sleep-manager-config.json`

Most important settings:

- `API_KEY`: shared secret for all authenticated endpoints
- `SLEEPER.name`: hostname used for sleeper API URLs
- `SLEEPER.mac_address`: MAC address used for Wake-on-LAN
- `WAKER.name`: hostname used for waker API URLs
- `WAKER.wol_exec`: path to `etherwake`
- `DOMAIN` and `PORT`: used to construct URLs for inter-machine calls

See the example config in `config/sleep-manager-config.json.example`.

## Documentation

Full installation, configuration, operations, troubleshooting, and API docs are published via GitHub Pages.

## HomeKit Integration

See `homebridge-sleep-manager/` for HomeKit integration using the `homebridge-http-switch` plugin.

## License

BSD 2-clause License - see LICENSE file for details.
