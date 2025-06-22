# System Requirements

System requirements and compatibility information for Sleep Manager.

## Hardware Requirements

### Sleeper Machine
- **Network Interface**: Wake-on-LAN capable Ethernet adapter
- **BIOS/UEFI**: Support for Wake-on-LAN (Power on by PCI-E)
- **Power Supply**: Must remain powered when suspended

### Waker Machine
- **Network Interface**: Any Ethernet or WiFi adapter
- **Software**: etherwake package for sending WoL packets

## Software Requirements

### Operating System
- **Debian 12 (Bookworm)** or compatible Linux distribution
- **systemd** for service management
- **Python 3.8+** for application runtime

### Required Packages

**For Sleeper**:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ethtool systemd systemctl
```

**For Waker**:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip etherwake
```

## Network Requirements

- Both machines must be on the same local network
- Hostname resolution must work between machines
- Port 51339 must be accessible between machines

## BIOS/UEFI Configuration

### Wake-on-LAN Setup

1. Restart the sleeper machine and enter BIOS/UEFI
2. Navigate to Power Management or Advanced settings
3. Enable "Wake on PCI-E", "Wake on LAN", or "Power on by PCI-E"
4. Save changes and exit
5. Verify: `sudo ethtool eth0 | grep -i wake`

## System Configuration

### Automated Setup

The setup script handles most configuration automatically:

```bash
# Setup machines
sudo ./scripts/setup-system.sh sleeper
sudo ./scripts/setup-system.sh waker
sudo ./scripts/setup-system.sh both

# Check status
sudo ./scripts/setup-system.sh status
```

### Manual Configuration

The setup script creates:
- `sleep-manager` system user
- `/usr/local/sleep-manager` application directory
- Python virtual environment
- Systemd services and network configuration

## Security Considerations

- Application runs as `sleep-manager` system user with minimal privileges
- API key authentication required for all operations
- HTTP only (acceptable for local networks)
- No external network access required

## Verification Steps

```bash
# Check system requirements
python3 --version
systemctl --version
which etherwake

# Test Wake-on-LAN
sudo ethtool eth0 | grep -i wake
sudo etherwake AA:BB:CC:DD:EE:FF

# Verify network connectivity
nslookup sleeper_url
ping sleeper_url

# Check service status
sudo ./scripts/setup-system.sh status
sudo systemctl status sleep-manager-sleeper sleep-manager-waker
```

## Troubleshooting

### Common Issues

1. **Wake-on-LAN not working**
   - Verify BIOS/UEFI settings
   - Check network interface WoL status
   - Ensure power supply remains active

2. **Service won't start**
   - Check Python virtual environment
   - Verify configuration file
   - Check user permissions

3. **Network connectivity issues**
   - Verify hostname resolution
   - Check firewall settings
   - Test with ping/telnet

### Diagnostic Commands

```bash
# Check system status
sudo ./scripts/setup-system.sh status

# View service logs
sudo journalctl -u sleep-manager-sleeper -f
sudo journalctl -u sleep-manager-waker -f

# Test API endpoints
curl http://localhost:51339/status
```

## Maintenance

```bash
# Update dependencies
sudo ./scripts/setup-system.sh update-deps

# Monitor logs
sudo journalctl -u sleep-manager-* --since "1 day ago"

# Check service health
sudo ./scripts/setup-system.sh status
```

## Uninstallation

```bash
# Remove specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Remove everything
sudo ./scripts/setup-system.sh uninstall-all
```

**Note**: Application files in `/usr/local/sleep-manager` are preserved for easy reinstallation. 