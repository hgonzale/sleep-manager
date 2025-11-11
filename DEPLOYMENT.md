# Deployment Guide

Detailed deployment instructions for Sleep Manager on Debian 12 systems.

## Prerequisites

- Debian 12 system
- Root access (sudo)
- Python 3.10 or higher
- Network connectivity between machines

## Automated Setup

```bash
# Clone and setup
git clone <repository-url>
cd sleep-manager
chmod +x scripts/setup-system.sh

# Setup machines
sudo ./scripts/setup-system.sh sleeper  # Machine that will be suspended
sudo ./scripts/setup-system.sh waker    # Machine that will wake the sleeper
sudo ./scripts/setup-system.sh both     # Both services on same machine
```

## Configuration

Create configuration file:
```bash
sudo mkdir -p /usr/local/sleep-manager/config
sudo nano /usr/local/sleep-manager/config/sleep-manager-config.json
```

Example configuration:
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

## Service Management

```bash
# Start and enable services
sudo systemctl start sleep-manager-sleeper sleep-manager-waker
sudo systemctl enable sleep-manager-sleeper sleep-manager-waker

# Check status
sudo systemctl status sleep-manager-sleeper sleep-manager-waker

# View logs
sudo journalctl -u sleep-manager-* -f
```

## Manual Configuration

### BIOS/UEFI Wake-on-LAN Setup

1. Restart and enter BIOS/UEFI settings
2. Navigate to Power Management or Advanced settings
3. Enable "Wake on PCI-E" or "Wake on LAN"
4. Save changes and restart

### Network Interface Configuration

The setup script configures Wake-on-LAN automatically. For manual configuration:

```bash
# Check WoL status
sudo ethtool eth0

# Enable WoL manually
sudo ethtool -s eth0 wol g

# Create persistent configuration
sudo nano /etc/systemd/network/25-wol-eth0.network
```

Add content:
```
[Match]
Name=eth0

[Link]
WakeOnLan=magic
```

## Testing

```bash
# Test wake
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

# Test suspend
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend

# Check status
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status sleep-manager-sleeper
   sudo journalctl -u sleep-manager-sleeper -n 50
   ```

2. **Wake-on-LAN not working**
   ```bash
   sudo ethtool eth0 | grep -i wake
   sudo etherwake AA:BB:CC:DD:EE:FF
   ```

3. **Network connectivity issues**
   ```bash
   sudo ./scripts/setup-system.sh status
   ping sleeper_url
   ```

### Uninstallation

```bash
# Remove specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Remove everything
sudo ./scripts/setup-system.sh uninstall-all
```

## Security

- Change default API key in configuration
- Use HTTPS in production environments
- Configure firewall rules appropriately
- Regularly update dependencies

## Maintenance

```bash
# Update dependencies
sudo ./scripts/setup-system.sh update-deps

# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/

# Monitor services
sudo ./scripts/setup-system.sh status
```

## Next Steps

- [System Requirements](SYSTEM_REQUIREMENTS.md) for additional configuration
- [Quick Reference](QUICK_REFERENCE.md) for common commands
- [API Documentation](docs/_build/html/index.html) for endpoint details 
