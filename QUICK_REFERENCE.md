# Sleep Manager Quick Reference

Quick reference guide for common Sleep Manager commands and operations.

## Setup Script Commands

### Basic Setup
```bash
# Setup Sleeper (machine that will be suspended)
sudo ./scripts/setup-system.sh sleeper

# Setup Waker (machine that will wake the sleeper)
sudo ./scripts/setup-system.sh waker

# Setup Both (if running both services on same machine)
sudo ./scripts/setup-system.sh both
```

### Status and Maintenance
```bash
# Show current status
sudo ./scripts/setup-system.sh status

# Update Python dependencies
sudo ./scripts/setup-system.sh update-deps

# Show help
./scripts/setup-system.sh help
```

### Uninstallation
```bash
# Remove specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Remove everything
sudo ./scripts/setup-system.sh uninstall-all
```

## Service Management

### Start Services
```bash
# Start services
sudo systemctl start sleep-manager-sleeper
sudo systemctl start sleep-manager-waker

# Enable auto-start
sudo systemctl enable sleep-manager-sleeper
sudo systemctl enable sleep-manager-waker
```

### Stop Services
```bash
# Stop services
sudo systemctl stop sleep-manager-sleeper
sudo systemctl stop sleep-manager-waker

# Disable auto-start
sudo systemctl disable sleep-manager-sleeper
sudo systemctl disable sleep-manager-waker
```

### Check Status
```bash
# Check service status
sudo systemctl status sleep-manager-sleeper
sudo systemctl status sleep-manager-waker

# Check if services are enabled
sudo systemctl is-enabled sleep-manager-sleeper
sudo systemctl is-enabled sleep-manager-waker
```

## API Operations

### Status Checks
```bash
# Check sleeper status
curl http://sleeper_url:51339/status

# Check waker status
curl http://waker_url:51339/status
```

### Suspend Operations
```bash
# Suspend sleeper (from waker)
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/suspend

# Suspend sleeper directly
curl -H "X-API-Key: your-api-key" \
     -X POST http://sleeper_url:51339/suspend
```

### Wake Operations
```bash
# Wake sleeper (from waker)
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/wake
```

## Configuration

### Configuration File Location
```bash
# Main configuration file
/usr/local/sleep-manager/config/sleep-manager-config.json

# Example configuration
/usr/local/sleep-manager/config/sleep-manager-config.json.example
```

### Edit Configuration
```bash
# Edit configuration
sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json

# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
```

## Monitoring and Logs

### View Logs
```bash
# View service logs in real-time
sudo journalctl -u sleep-manager-sleeper -f
sudo journalctl -u sleep-manager-waker -f

# View recent logs
sudo journalctl -u sleep-manager-sleeper --since "1 hour ago"
sudo journalctl -u sleep-manager-waker --since "1 hour ago"

# View all sleep-manager logs
sudo journalctl -u sleep-manager-* -f
```

### System Status
```bash
# Check overall system status
sudo ./scripts/setup-system.sh status

# Check Wake-on-LAN status
sudo ethtool eth0 | grep -i wake

# Check network connectivity
ping sleeper_url
ping waker_url
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status sleep-manager-sleeper

# Check logs
sudo journalctl -u sleep-manager-sleeper -n 50

# Check configuration
sudo cat /usr/local/sleep-manager/config/sleep-manager-config.json
```

#### Wake-on-LAN Not Working
```bash
# Check WoL status
sudo ethtool eth0 | grep -i wake

# Test WoL manually
sudo etherwake AA:BB:CC:DD:EE:FF

# Check BIOS settings (reboot required)
# Enter BIOS and enable Wake-on-LAN
```

#### Network Issues
```bash
# Check hostname resolution
nslookup sleeper_url
nslookup waker_url

# Test connectivity
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

### Run Tests
```bash
# Run all tests
./scripts/run-tests.sh

# Run specific tests
python -m pytest tests/test_sleeper.py
python -m pytest tests/test_waker.py
python -m pytest tests/test_integration.py
```

### Development Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Run tests
pytest
```

## File Locations

### Application Files
```
/usr/local/sleep-manager/           # Application directory
├── config/                         # Configuration files
│   ├── sleep-manager-config.json
│   └── sleep-manager-config.json.example
├── venv/                          # Python virtual environment
├── sleep-manager/                 # Application code
│   ├── __init__.py
│   ├── sleeper.py
│   └── waker.py
└── tests/                         # Test files
    ├── test_sleeper.py
    ├── test_waker.py
    └── test_integration.py
```

### System Files
```
/etc/systemd/system/               # Systemd service files
├── sleep-manager-sleeper.service
├── sleep-manager-waker.service
└── sleep-manager-delay.service

/etc/systemd/network/              # Network configuration
└── 25-wol-*.network              # Wake-on-LAN configs
```

### Log Files
```
/var/log/                          # System logs
└── journal/                       # systemd journal logs
```

## Environment Variables

### Optional Environment Variables
```bash
# Flask environment
export FLASK_ENV=development

# Python path
export PYTHONPATH=/usr/local/sleep-manager

# Log level
export LOG_LEVEL=DEBUG
```

## Security

### API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Update API key in configuration
sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json
```

### User Permissions
```bash
# Check sleep-manager user
id sleep-manager

# Check file permissions
ls -la /usr/local/sleep-manager/

# Check service user
sudo systemctl show sleep-manager-sleeper | grep User
```

## Backup and Recovery

### Backup
```bash
# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/

# Backup systemd services
sudo cp /etc/systemd/system/sleep-manager-*.service /backup/

# Backup network configuration
sudo cp /etc/systemd/network/25-wol-*.network /backup/
```

### Recovery
```bash
# Restore configuration
sudo cp /backup/sleep-manager-config.json /usr/local/sleep-manager/config/

# Restart services
sudo systemctl restart sleep-manager-sleeper
sudo systemctl restart sleep-manager-waker
```

## Performance

### Resource Usage
```bash
# Check memory usage
ps aux | grep sleep-manager

# Check disk usage
du -sh /usr/local/sleep-manager/

# Check network connections
netstat -tlnp | grep 51339
```

### Optimization
```bash
# Update dependencies
sudo ./scripts/setup-system.sh update-deps

# Restart services
sudo systemctl restart sleep-manager-*

# Clear old logs
sudo journalctl --vacuum-time=7d
``` 