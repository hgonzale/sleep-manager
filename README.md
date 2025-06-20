# Sleep Manager

A Flask-based application for managing sleep/wake cycles between two machines on a local network. The system consists of a "sleeper" machine that can be suspended and woken remotely, and a "waker" machine that sends Wake-on-LAN packets to wake the sleeper.

## Features

- **Remote Suspend**: Suspend the sleeper machine via HTTP API
- **Wake-on-LAN**: Wake the sleeper machine remotely
- **Status Monitoring**: Check the status of both machines
- **API Key Authentication**: Secure API access
- **Systemd Integration**: Automatic service management
- **Debian 12 Support**: Optimized for Debian 12 systems
- **Documentation-as-Code**: API documentation generated from docstrings

## Architecture

```
[Waker Machine] ---- [Local Network] ---- [Sleeper Machine]
    (waker_url)                              (sleeper_url)
```

- **Sleeper**: Runs Flask app on port 51339, can be suspended via API
- **Waker**: Runs Flask app on port 51339, sends Wake-on-LAN packets
- **Communication**: HTTP API with API key authentication

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sleep-manager
chmod +x scripts/setup-system.sh
```

### 2. Setup Machines

#### Setup Sleeper (machine that will be suspended)
```bash
sudo ./scripts/setup-system.sh sleeper
```

#### Setup Waker (machine that will wake the sleeper)
```bash
sudo ./scripts/setup-system.sh waker
```

#### Setup Both (if running both services on same machine)
```bash
sudo ./scripts/setup-system.sh both
```

### 3. Configure the Application

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
# Start services
sudo systemctl start sleep-manager-sleeper
sudo systemctl start sleep-manager-waker

# Enable auto-start
sudo systemctl enable sleep-manager-sleeper
sudo systemctl enable sleep-manager-waker
```

### 5. Test the Setup

```bash
# Test sleeper status
curl http://sleeper_url:51339/status

# Test waker status
curl http://waker_url:51339/status

# Test suspend (from waker)
curl -H "X-API-Key: your-secure-api-key-here" \
     http://waker_url:51339/suspend

# Test wake (from waker)
curl -H "X-API-Key: your-secure-api-key-here" \
     http://waker_url:51339/wake
```

## System Requirements

- **Operating System**: Debian 12 (Bookworm) or compatible Linux
- **Python**: 3.8 or higher
- **Network**: Both machines on same local network
- **Hardware**: Wake-on-LAN capable network interface (sleeper)

For detailed system requirements and setup procedures, see [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md).

## Installation

### Automated Installation

The setup script handles most configuration automatically:

```bash
# Show available commands
./scripts/setup-system.sh help

# Setup specific components
sudo ./scripts/setup-system.sh sleeper
sudo ./scripts/setup-system.sh waker

# Check status
sudo ./scripts/setup-system.sh status

# Update dependencies
sudo ./scripts/setup-system.sh update-deps
```

### Manual Installation

For manual installation steps, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Configuration

### Configuration File

The application uses a JSON configuration file located at `/usr/local/sleep-manager/config/sleep-manager-config.json`.

### Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `WAKER.name` | Hostname of the waker machine | `"waker_url"` |
| `WAKER.ip` | IP address of the waker machine | `"192.168.1.100"` |
| `WAKER.mac` | MAC address of the waker machine | `"00:11:22:33:44:55"` |
| `SLEEPER.name` | Hostname of the sleeper machine | `"sleeper_url"` |
| `SLEEPER.ip` | IP address of the sleeper machine | `"192.168.1.101"` |
| `SLEEPER.mac` | MAC address of the sleeper machine | `"AA:BB:CC:DD:EE:FF"` |
| `API_KEY` | Secret key for API authentication | `"your-secure-key"` |

## API Reference

The Sleep Manager provides a comprehensive REST API with the following endpoints:

- **Health Check**: `GET /health` - Check application health
- **Sleeper Endpoints**: `/sleeper/*` - Control sleeper machine
- **Waker Endpoints**: `/waker/*` - Control waker operations

### Quick API Examples

```bash
# Check health
curl http://sleeper_url:51339/health

# Get sleeper status
curl -H "X-API-Key: your-api-key" http://sleeper_url:51339/sleeper/status

# Wake sleeper from waker
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/wake

# Suspend sleeper from waker
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/suspend
```

For complete API documentation, see the [Documentation](#documentation) section below.

## Documentation

The Sleep Manager uses **documentation-as-code** - all API documentation is generated directly from the source code docstrings using Sphinx.

### Building Documentation

```bash
# Install documentation dependencies
pip install -e .[docs]

# Build documentation
./scripts/build-docs.sh build

# Serve documentation locally
./scripts/build-docs.sh serve

# Clean build files
./scripts/build-docs.sh clean
```

### Documentation Structure

- **API Reference**: Automatically generated from Flask route docstrings
- **Installation Guide**: Step-by-step installation instructions
- **Quick Start**: Get up and running in minutes
- **Configuration**: Detailed configuration options
- **Deployment**: Production deployment guide
- **Troubleshooting**: Common issues and solutions

### Documentation Features

- **Auto-generated API docs**: Always in sync with the code
- **Interactive examples**: Copy-paste ready code samples
- **Search functionality**: Find what you need quickly
- **Multiple formats**: HTML and PDF output
- **Cross-references**: Links between related topics

## Usage Examples

### Basic Operations

```bash
# Check if sleeper is running
curl http://sleeper_url:51339/health

# Suspend sleeper from waker
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/waker/suspend

# Wake sleeper from waker
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/waker/wake
```

### Script Integration

```bash
#!/bin/bash
# Example script to suspend at night and wake in morning

# Suspend at 10 PM
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/waker/suspend

# Wake at 8 AM
curl -H "X-API-Key: your-api-key" \
     -X POST http://waker_url:51339/waker/wake
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

### Getting Help

1. Check the troubleshooting section in [DEPLOYMENT.md](DEPLOYMENT.md)
2. Review [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md)
3. Check service logs: `sudo journalctl -u sleep-manager-* -f`
4. Run status check: `sudo ./scripts/setup-system.sh status`
5. Build and browse the documentation: `./scripts/build-docs.sh serve`

## Security

- **API Key Authentication**: All sensitive operations require API key
- **Local Network Only**: Application designed for local network use
- **Minimal Privileges**: Runs as dedicated system user
- **No External Access**: No internet connectivity required

## Maintenance

### Regular Tasks

```bash
# Update dependencies
sudo ./scripts/setup-system.sh update-deps

# Check service status
sudo ./scripts/setup-system.sh status

# Monitor logs
sudo journalctl -u sleep-manager-* -f

# Update documentation
./scripts/build-docs.sh build
```

### Backup

```bash
# Backup configuration
sudo cp /usr/local/sleep-manager/config/sleep-manager-config.json /backup/
```

## Development

### Running Tests

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test files
python -m pytest tests/test_sleeper.py
python -m pytest tests/test_waker.py
```

### Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .[dev,docs]

# Run tests
pytest

# Build documentation
./scripts/build-docs.sh build
```

### Code Quality

```bash
# Format code
black sleep-manager/

# Lint code
flake8 sleep-manager/

# Type checking
mypy sleep-manager/
```

## Uninstallation

```bash
# Remove specific components
sudo ./scripts/setup-system.sh uninstall-sleeper
sudo ./scripts/setup-system.sh uninstall-waker

# Remove everything
sudo ./scripts/setup-system.sh uninstall-all
```

**Note**: Application files are preserved for easy reinstallation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation (docstrings for API changes)
6. Run the test suite
7. Build documentation to verify changes
8. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the documentation
2. Review troubleshooting guides
3. Open an issue on the repository

## Documentation

- [API Documentation](docs/_build/html/index.html) - Complete API reference (build with `./scripts/build-docs.sh build`)
- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment instructions
- [System Requirements](SYSTEM_REQUIREMENTS.md) - System requirements and setup
- [Quick Reference](QUICK_REFERENCE.md) - Common commands and examples
- [Changelog](CHANGELOG.md) - Version history and changes 