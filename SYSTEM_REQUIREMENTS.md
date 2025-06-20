# System Requirements for Sleep Manager

This document outlines the system requirements and setup procedures for the Sleep Manager application on Debian 12.

## Overview

The Sleep Manager consists of two components:
- **Sleeper**: Machine that can be suspended and woken remotely
- **Waker**: Machine that sends Wake-on-LAN packets to wake the sleeper

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

#### For Sleeper
```bash
# Core system packages
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Network tools
sudo apt install -y ethtool

# System management
sudo apt install -y systemd systemctl
```

#### For Waker
```bash
# Core system packages
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Wake-on-LAN tool
sudo apt install -y etherwake
```

## Network Requirements

### Network Configuration
- Both machines must be on the same local network
- Hostname resolution must work between machines
- Port 51339 must be accessible between machines

### Hostname Resolution
The setup script will automatically check if hostname resolution is working correctly between the machines. If issues are detected, the script will provide guidance on how to resolve them.

## BIOS/UEFI Configuration

### Wake-on-LAN Setup

1. **Access BIOS/UEFI**
   - Restart the sleeper machine
   - Enter BIOS/UEFI (usually F2, F10, Del, or Esc)
   - Navigate to Power Management or Advanced settings

2. **Enable Wake-on-LAN**
   - Look for "Wake on PCI-E", "Wake on LAN", or "Power on by PCI-E"
   - Enable this option
   - Save changes and exit

3. **Verify Settings**
   - Boot into the operating system
   - Check Wake-on-LAN status: `sudo ethtool eth0 | grep -i wake`

## System Configuration

### Automated Setup

The setup script handles most configuration automatically:

```bash
# Setup Sleeper machine
sudo ./scripts/setup-system.sh sleeper

# Setup Waker machine
sudo ./scripts/setup-system.sh waker

# Setup Both (if running both services on same machine)
sudo ./scripts/setup-system.sh both

# Check status
sudo ./scripts/setup-system.sh status
```

### Manual Configuration Steps

#### 1. User and Directory Setup

The setup script creates:
- `sleep-manager` system user
- `/usr/local/sleep-manager` application directory
- Python virtual environment

#### 2. Wake-on-LAN Configuration

The setup script automatically:
- Enables Wake-on-LAN on the primary network interface
- Creates systemd-networkd configuration for persistence
- Restarts systemd-networkd to apply changes

#### 3. Systemd Services

The setup script installs:
- `sleep-manager-sleeper.service` - Flask application for sleeper
- `sleep-manager-waker.service` - Flask application for waker
- `sleep-manager-delay.service` - Suspend delay service

## Security Considerations

### User Permissions
- Application runs as `sleep-manager` system user
- Minimal required privileges
- No sudo access for application user

### Network Security
- API key authentication required
- HTTP only (acceptable for local networks)
- No external network access required

### System Security
- Application files owned by `sleep-manager` user
- Configuration files protected with appropriate permissions
- Systemd services run with security restrictions

## Verification Steps

### 1. Check System Requirements

```bash
# Verify Python version
python3 --version

# Check systemctl availability
systemctl --version

# Verify etherwake installation (waker only)
which etherwake
```

### 2. Test Wake-on-LAN

```bash
# Check WoL status
sudo ethtool eth0 | grep -i wake

# Test WoL manually (from waker to sleeper)
sudo etherwake AA:BB:CC:DD:EE:FF
```

### 3. Verify Network Connectivity

```bash
# Check hostname resolution
nslookup sleeper_url
nslookup waker_url

# Test connectivity
ping sleeper_url
ping waker_url
```

### 4. Check Service Status

```bash
# Check service status
sudo ./scripts/setup-system.sh status

# Check individual services
sudo systemctl status sleep-manager-sleeper
sudo systemctl status sleep-manager-waker
```

## Troubleshooting

### Common Issues

1. **Wake-on-LAN Not Working**
   - Verify BIOS/UEFI settings
   - Check network interface WoL status
   - Ensure power supply remains active

2. **Service Won't Start**
   - Check Python virtual environment
   - Verify configuration file
   - Check user permissions

3. **Network Connectivity Issues**
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

### Regular Tasks

1. **Update Dependencies**
   ```bash
   sudo ./scripts/setup-system.sh update-deps
   ```

2. **Monitor Logs**
   ```bash
   sudo journalctl -u sleep-manager-* --since "1 day ago"
   ```

3. **Check Service Health**
   ```bash
   sudo ./scripts/setup-system.sh status
   ```

### Backup

Backup important configuration:
```bash
# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/

# Backup systemd services
sudo cp /etc/systemd/system/sleep-manager-*.service /backup/
```

## Uninstallation

### Remove Components

```bash
# Remove specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Remove everything
sudo ./scripts/setup-system.sh uninstall-all
```

**Note**: Application files in `/usr/local/sleep-manager` are preserved for easy reinstallation.

## Support

For system requirement issues:
1. Check this document for troubleshooting steps
2. Verify BIOS/UEFI settings
3. Test network connectivity
4. Review service logs
5. Check the deployment guide for additional help 