# Sleep Manager Deployment Guide

This guide covers deploying the Sleep Manager application on Debian 12 systems.

## Prerequisites

- Debian 12 system
- Root access (sudo)
- Python 3.8 or higher
- Network connectivity between machines

## Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd sleep-manager

# Make setup script executable
chmod +x scripts/setup-system.sh
```

### 2. Run Setup Script

The setup script now uses command-line arguments instead of interactive menus:

```bash
# Setup Sleeper (machine that will be suspended)
sudo ./scripts/setup-system.sh sleeper

# Setup Waker (machine that will wake the sleeper)
sudo ./scripts/setup-system.sh waker

# Setup Both (if running both services on same machine)
sudo ./scripts/setup-system.sh both

# Show current status
sudo ./scripts/setup-system.sh status

# Get help
./scripts/setup-system.sh help
```

### 3. Configuration

Create the configuration file:

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

### 4. Start Services

```bash
# Start Sleeper service
sudo systemctl start sleep-manager-sleeper

# Start Waker service
sudo systemctl start sleep-manager-waker

# Check status
sudo systemctl status sleep-manager-sleeper
sudo systemctl status sleep-manager-waker
```

## Manual Configuration Steps

### BIOS/UEFI Wake-on-LAN Setup

1. **Access BIOS/UEFI**: Restart and enter BIOS/UEFI settings
2. **Power Management**: Navigate to Power Management or Advanced settings
3. **Wake-on-LAN**: Enable "Wake on PCI-E" or "Wake on LAN"
4. **Save and Exit**: Save changes and restart

### Network Interface Configuration

The setup script automatically configures Wake-on-LAN for the primary network interface. If you need to configure additional interfaces:

```bash
# Check current WoL status
sudo ethtool eth0

# Enable WoL manually
sudo ethtool -s eth0 wol g

# Create persistent configuration
sudo nano /etc/systemd/network/25-wol-eth0.network
```

Add the following content:

```
[Match]
Name=eth0

[Link]
WakeOnLan=magic
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

### View Logs

```bash
# View service logs
sudo journalctl -u sleep-manager-sleeper -f
sudo journalctl -u sleep-manager-waker -f

# View recent logs
sudo journalctl -u sleep-manager-sleeper --since "1 hour ago"
```

## Testing

### Test Sleeper Service

```bash
# Test suspend endpoint
curl -H "X-API-Key: your-secure-api-key-here" \
     http://sleeper_url:51339/suspend

# Test status endpoint
curl http://sleeper_url:51339/status
```

### Test Waker Service

```bash
# Test wake endpoint
curl -H "X-API-Key: your-secure-api-key-here" \
     http://waker_url:51339/wake

# Test status endpoint
curl http://waker_url:51339/status
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check service status
   sudo systemctl status sleep-manager-sleeper
   
   # Check logs
   sudo journalctl -u sleep-manager-sleeper -n 50
   ```

2. **Wake-on-LAN not working**
   ```bash
   # Check WoL status
   sudo ethtool eth0
   
   # Test WoL manually
   sudo etherwake AA:BB:CC:DD:EE:FF
   ```

3. **Network connectivity issues**
   ```bash
   # Check hostname resolution
   sudo ./scripts/setup-system.sh status
   
   # Test connectivity
   ping sleeper_url
   ```

### Uninstallation

```bash
# Uninstall specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Uninstall everything
sudo ./scripts/setup-system.sh uninstall-all
```

## Security Considerations

- Change the default API key in the configuration
- Use HTTPS in production environments
- Configure firewall rules appropriately
- Regularly update dependencies

## Maintenance

### Update Dependencies

```bash
# Update Python packages
sudo ./scripts/setup-system.sh update-deps
```

### Backup Configuration

```bash
# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
```

### Monitor Services

```bash
# Check service status
sudo ./scripts/setup-system.sh status

# Monitor logs
sudo journalctl -u sleep-manager-* -f
```

## Next Steps

After deployment, refer to:
- [API Documentation](API.md) for endpoint details
- [System Requirements](SYSTEM_REQUIREMENTS.md) for additional configuration
- [Quick Reference](QUICK_REFERENCE.md) for common commands 