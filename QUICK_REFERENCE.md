# Quick Reference

Quick reference guide for common Sleep Manager commands and operations.

## Setup Script Commands

```bash
# Setup machines
sudo ./scripts/setup-system.sh sleeper  # Machine that will be suspended
sudo ./scripts/setup-system.sh waker    # Machine that will wake the sleeper
sudo ./scripts/setup-system.sh both     # Both services on same machine

# Status and maintenance
sudo ./scripts/setup-system.sh status
sudo ./scripts/setup-system.sh update-deps
./scripts/setup-system.sh help

# Uninstallation
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker
sudo ./scripts/setup-system.sh uninstall-all
```

## Service Management

```bash
# Start and enable services
sudo systemctl start sleep-manager-sleeper sleep-manager-waker
sudo systemctl enable sleep-manager-sleeper sleep-manager-waker

# Stop and disable services
sudo systemctl stop sleep-manager-sleeper sleep-manager-waker
sudo systemctl disable sleep-manager-sleeper sleep-manager-waker

# Check status
sudo systemctl status sleep-manager-sleeper sleep-manager-waker
sudo systemctl is-enabled sleep-manager-sleeper sleep-manager-waker
```

## API Operations

```bash
# Status checks
curl http://sleeper_url:51339/status
curl http://waker_url:51339/status

# Suspend operations
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend
curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/suspend

# Wake operations
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake
```

## Configuration

```bash
# Configuration file location
/usr/local/sleep-manager/config/sleep-manager-config.json

# Edit configuration
sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
```

## Monitoring and Logs

```bash
# View logs in real-time
sudo journalctl -u sleep-manager-sleeper -f
sudo journalctl -u sleep-manager-waker -f
sudo journalctl -u sleep-manager-* -f

# View recent logs
sudo journalctl -u sleep-manager-sleeper --since "1 hour ago"

# Check system status
sudo ./scripts/setup-system.sh status
sudo ethtool eth0 | grep -i wake
ping sleeper_url
```

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
sudo systemctl status sleep-manager-sleeper
sudo journalctl -u sleep-manager-sleeper -n 50
sudo cat /usr/local/sleep-manager/config/sleep-manager-config.json
```

**Wake-on-LAN not working**:
```bash
sudo ethtool eth0 | grep -i wake
sudo etherwake AA:BB:CC:DD:EE:FF
# Check BIOS settings (reboot required)
```

**Network issues**:
```bash
nslookup sleeper_url
ping sleeper_url
telnet sleeper_url 51339
```

### Diagnostic Commands

```bash
# Check Python virtual environment
ls -la /usr/local/sleep-manager/venv/

# Check user permissions
id sleep-manager
ls -la /usr/local/sleep-manager/

# Check systemd services
systemctl list-units --type=service | grep sleep-manager
```

## Development

```bash
# Run tests
./scripts/run-tests.sh
python -m pytest tests/test_sleeper.py
python -m pytest tests/test_waker.py

# Development setup
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
pytest
```

## File Locations

```
/usr/local/sleep-manager/           # Application directory
├── config/                         # Configuration files
├── venv/                          # Python virtual environment
└── sleep-manager/                 # Application code

/etc/systemd/system/               # Systemd service files
├── sleep-manager-sleeper.service
├── sleep-manager-waker.service
└── sleep-manager-delay.service
```

## Security

```bash
# Generate secure API key
openssl rand -hex 32

# Check user permissions
id sleep-manager
ls -la /usr/local/sleep-manager/
sudo systemctl show sleep-manager-sleeper | grep User
```

## Backup and Recovery

```bash
# Backup
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
sudo cp /etc/systemd/system/sleep-manager-*.service /backup/

# Recovery
sudo cp /backup/sleep-manager-config.json /usr/local/sleep-manager/config/
sudo systemctl restart sleep-manager-sleeper sleep-manager-waker
```

## Performance

```bash
# Check resource usage
ps aux | grep sleep-manager
du -sh /usr/local/sleep-manager/
netstat -tlnp | grep 51339

# Optimization
sudo ./scripts/setup-system.sh update-deps
sudo systemctl restart sleep-manager-*
sudo journalctl --vacuum-time=7d
``` 