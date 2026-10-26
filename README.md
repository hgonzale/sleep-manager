# Sleep Manager

Sleep Manager controls sleep/wake cycles between two machines on the same LAN. A **waker** sends Wake-on-LAN packets; a **sleeper** suspends itself on demand. Both run the same Flask app — the active role is inferred from the hostname matching `waker.name` or `sleeper.name` in config.

## Requirements

- Python 3.11+
- Two Linux machines with systemd on the same LAN
- Wake-on-LAN capable NIC on the sleeper
- `etherwake` and `ethtool` installed on the waker

## Install (Debian)

Add the [honkeandpastrami apt repository](https://github.com/honkeandpastrami/debian-repo) and install; `apt upgrade` picks up new releases:

```bash
sudo curl -fsSLo /etc/apt/keyrings/honkeandpastrami.pgp https://honkeandpastrami.github.io/debian-repo/honkeandpastrami.pgp
printf 'Types: deb\nURIs: https://honkeandpastrami.github.io/debian-repo\nSuites: stable\nComponents: main\nSigned-By: /etc/apt/keyrings/honkeandpastrami.pgp\n' \
  | sudo tee /etc/apt/sources.list.d/honkeandpastrami.sources
sudo apt update && sudo apt install sleep-manager
```

## Documentation

Full installation, configuration, operations, troubleshooting, and API docs: [https://hgonzale.github.io/sleep-manager/](https://hgonzale.github.io/sleep-manager/)

## HomeKit Integration

See [`homebridge-sleep-manager/`](homebridge-sleep-manager/README.md) for the custom Homebridge plugin (Homebridge ≥ 2.0).

## License

BSD 2-clause — see LICENSE.
