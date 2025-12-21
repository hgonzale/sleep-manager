#!/bin/bash

# Sleep Manager System Setup Script (Legacy)
# This script is a fallback for non-Debian/manual installs and is not the
# preferred path on Debian (use the .deb package instead). It assumes systemd.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Sleep Manager System Setup Script"
    echo "================================="
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  sleeper     Setup Sleeper (machine that will be suspended)"
    echo "  waker       Setup Waker (machine that will wake the sleeper)"
    echo "  both        Setup Both (if running both services on same machine)"
    echo "  uninstall-sleeper  Uninstall Sleeper components"
    echo "  uninstall-waker    Uninstall Waker components"
    echo "  uninstall-all      Uninstall All components"
    echo "  update-deps        Update Python dependencies"
    echo "  status             Show current status"
    echo "  help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 sleeper"
    echo "  $0 waker"
    echo "  $0 status"
    echo "  $0 uninstall-all"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to configure sudoers for sleep-manager runtime commands
configure_sudoers() {
    local role="$1"
    local sudoers_path="/etc/sudoers.d/sleep-manager"
    local systemctl_path=""
    local etherwake_path=""
    local tmp_file=""
    local -a existing_lines=()
    local -a new_lines=()

    if command_exists systemctl; then
        systemctl_path=$(command -v systemctl)
    fi

    if command_exists etherwake; then
        etherwake_path=$(command -v etherwake)
    fi

    if [[ -f "$sudoers_path" ]]; then
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            [[ "$line" =~ ^# ]] && continue
            existing_lines+=("$line")
        done < "$sudoers_path"
    fi

    if [[ "$role" == "sleeper" || "$role" == "both" ]]; then
        if [[ -n "$systemctl_path" ]]; then
            new_lines+=("sleep-manager ALL=(root) NOPASSWD: ${systemctl_path} suspend, ${systemctl_path} is-system-running")
        else
            print_warning "systemctl not found; skipping sudoers entry for sleeper commands."
        fi
    fi

    if [[ "$role" == "waker" || "$role" == "both" ]]; then
        if [[ -n "$etherwake_path" ]]; then
            new_lines+=("sleep-manager ALL=(root) NOPASSWD: ${etherwake_path}")
        else
            print_warning "etherwake not found; skipping sudoers entry for waker commands."
        fi
    fi

    if [[ ${#existing_lines[@]} -eq 0 && ${#new_lines[@]} -eq 0 ]]; then
        print_warning "No sudoers entries to write; skipping sudoers configuration."
        return 0
    fi

    print_status "Configuring sudoers for sleep-manager..."
    tmp_file=$(mktemp)
    {
        echo "# Managed by sleep-manager setup-system.sh"
        printf "%s\n" "${existing_lines[@]}" "${new_lines[@]}" | awk 'NF && !seen[$0]++'
    } > "$tmp_file"
    chown root:root "$tmp_file"
    chmod 0440 "$tmp_file"
    mv "$tmp_file" "$sudoers_path"
    chown root:root "$sudoers_path"
    chmod 0440 "$sudoers_path"

    if command_exists visudo; then
        if ! visudo -c -f "$sudoers_path" >/dev/null 2>&1; then
            print_warning "visudo check failed for $sudoers_path; please review manually."
        fi
    fi
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to detect system type
detect_system() {
    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect operating system"
        exit 1
    fi
}

# Function to check hostname resolution
check_hostname_resolution() {
    print_status "Checking hostname resolution..."
    
    # Check if configuration file exists
    if [[ ! -f /etc/sleep-manager/sleep-manager-config.json ]]; then
        print_warning "Configuration file not found. Skipping hostname resolution check."
        print_warning "Please configure the application first, then run this check again."
        return 0
    fi
    
    # Extract hostnames from configuration
    local waker_hostname=""
    local sleeper_hostname=""
    
    if command_exists jq; then
        waker_hostname=$(jq -r '.WAKER.name' /etc/sleep-manager/sleep-manager-config.json 2>/dev/null || echo "")
        sleeper_hostname=$(jq -r '.SLEEPER.name' /etc/sleep-manager/sleep-manager-config.json 2>/dev/null || echo "")
    else
        # Fallback to grep if jq is not available
        waker_hostname=$(grep -o '"name": *"[^"]*"' /etc/sleep-manager/sleep-manager-config.json | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
        sleeper_hostname=$(grep -o '"name": *"[^"]*"' /etc/sleep-manager/sleep-manager-config.json | tail -1 | cut -d'"' -f4 2>/dev/null || echo "")
    fi
    
    if [[ -z "$waker_hostname" || -z "$sleeper_hostname" ]]; then
        print_warning "Could not extract hostnames from configuration file."
        print_warning "Please ensure the configuration file contains valid WAKER.name and SLEEPER.name values."
        return 1
    fi
    
    print_status "Checking resolution for waker hostname: $waker_hostname"
    print_status "Checking resolution for sleeper hostname: $sleeper_hostname"
    
    local resolution_issues=0
    
    # Check waker hostname resolution
    if nslookup "$waker_hostname" >/dev/null 2>&1; then
        print_status "✓ Waker hostname '$waker_hostname' resolves correctly"
    else
        print_warning "✗ Waker hostname '$waker_hostname' does not resolve"
        resolution_issues=$((resolution_issues + 1))
    fi
    
    # Check sleeper hostname resolution
    if nslookup "$sleeper_hostname" >/dev/null 2>&1; then
        print_status "✓ Sleeper hostname '$sleeper_hostname' resolves correctly"
    else
        print_warning "✗ Sleeper hostname '$sleeper_hostname' does not resolve"
        resolution_issues=$((resolution_issues + 1))
    fi
    
    # Check connectivity between machines
    if [[ $resolution_issues -eq 0 ]]; then
        print_status "Testing connectivity between machines..."
        
        # Test ping to sleeper from waker (if this is the waker machine)
        if ping -c 1 "$sleeper_hostname" >/dev/null 2>&1; then
            print_status "✓ Can reach sleeper machine ($sleeper_hostname)"
        else
            print_warning "✗ Cannot reach sleeper machine ($sleeper_hostname)"
            print_warning "  This may indicate network connectivity issues"
        fi
        
        # Test ping to waker from sleeper (if this is the sleeper machine)
        if ping -c 1 "$waker_hostname" >/dev/null 2>&1; then
            print_status "✓ Can reach waker machine ($waker_hostname)"
        else
            print_warning "✗ Cannot reach waker machine ($waker_hostname)"
            print_warning "  This may indicate network connectivity issues"
        fi
    fi
    
    if [[ $resolution_issues -gt 0 ]]; then
        print_warning "Hostname resolution issues detected!"
        print_warning "To resolve these issues:"
        print_warning "1. Ensure both machines are on the same network"
        print_warning "2. Check DNS configuration or add entries to /etc/hosts"
        print_warning "3. Verify network connectivity between machines"
        print_warning "4. Ensure hostnames in configuration match actual machine hostnames"
        return 1
    else
        print_status "✓ Hostname resolution is working correctly"
        return 0
    fi
}

# Function to setup sleeper machine
setup_sleeper() {
    print_status "Setting up SLEEPER machine..."
    
    # Check systemctl
    if ! command_exists systemctl; then
        print_error "systemctl not found. This system may not be using systemd."
        exit 1
    fi
    print_status "systemctl found: $(which systemctl)"
    
    # Create sleep-manager user and group
    print_status "Creating sleep-manager user and group..."
    if ! id "sleep-manager" &>/dev/null; then
        useradd --system --user-group --shell /bin/false --home-dir /usr/lib/sleep-manager sleep-manager
        print_status "Created sleep-manager user"
    else
        print_status "sleep-manager user already exists"
    fi
    
    # Create application directory
    print_status "Setting up application directory..."
    mkdir -p /usr/lib/sleep-manager
    
    # Copy project files, excluding development-specific directories
    print_status "Copying project files..."
    cd "$PROJECT_DIR"
    for item in *; do
        # Skip venv, .git, and other development directories
        if [[ "$item" != "venv" && "$item" != ".git" && "$item" != "debian" && "$item" != "__pycache__" && "$item" != "*.pyc" ]]; then
            if [[ -d "$item" ]]; then
                cp -r "$item" /usr/lib/sleep-manager/
            else
                cp "$item" /usr/lib/sleep-manager/
            fi
        fi
    done
    
    # Setup configuration directory
    print_status "Setting up configuration directory..."
    mkdir -p /etc/sleep-manager

    if [[ ! -f /etc/sleep-manager/sleep-manager-config.json ]]; then
        if [[ -f /usr/lib/sleep-manager/config/sleep-manager-config.json ]]; then
            cp /usr/lib/sleep-manager/config/sleep-manager-config.json /etc/sleep-manager/sleep-manager-config.json
            chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json
            chmod 0640 /etc/sleep-manager/sleep-manager-config.json
            print_status "Migrated existing config to /etc/sleep-manager/sleep-manager-config.json"
        elif [[ -f /usr/local/sleep-manager/config/sleep-manager-config.json ]]; then
            cp /usr/local/sleep-manager/config/sleep-manager-config.json /etc/sleep-manager/sleep-manager-config.json
            chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json
            chmod 0640 /etc/sleep-manager/sleep-manager-config.json
            print_status "Migrated existing config to /etc/sleep-manager/sleep-manager-config.json"
        fi
    fi
    
    # Copy example configuration file if it exists
    if [[ -f "$PROJECT_DIR/config/sleep-manager-config.json.example" ]]; then
        cp "$PROJECT_DIR/config/sleep-manager-config.json.example" /etc/sleep-manager/sleep-manager-config.json.example
        print_status "Copied example configuration file to /etc/sleep-manager/"
        print_warning "Please edit /etc/sleep-manager/sleep-manager-config.json.example and rename it to sleep-manager-config.json"
        chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json.example
        chmod 0644 /etc/sleep-manager/sleep-manager-config.json.example
    else
        print_warning "Example configuration file not found. Please create /etc/sleep-manager/sleep-manager-config.json manually."
    fi
    
    chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager
    chmod 755 /usr/lib/sleep-manager

    # Create and configure virtual environment
    print_status "Setting up Python virtual environment..."
    if ! command_exists python3; then
        print_error "python3 not found. Please install Python 3 first."
        exit 1
    fi
    
    # Create virtual environment
    cd /usr/lib/sleep-manager
    python3 -m venv venv
    chown -R sleep-manager:sleep-manager venv
    
    # Install dependencies via the project metadata
    print_status "Installing Python dependencies..."
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install --upgrade pip
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install --upgrade -e .
    
    print_status "Virtual environment setup complete"
    
    if ethtool_available >/dev/null 2>&1; then
        print_status "ethtool found: $(ethtool_available)"
    else
        print_warning "ethtool not found. Please install it manually."
    fi
    
    # Install systemd delay service
    print_status "Installing systemd delay service..."
    cp "$PROJECT_DIR/systemd/sleep-manager-delay.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable sleep-manager-delay.service
    print_status "Systemd delay service installed and enabled"
    
    # Install Flask application service
    print_status "Installing Flask application service..."
    cp "$PROJECT_DIR/systemd/sleep-manager-sleeper.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable sleep-manager-sleeper.service
    print_status "Flask application service installed and enabled"
    
    configure_sudoers "sleeper"

    # Configure Wake-on-LAN
    print_status "Configuring Wake-on-LAN using NetworkManager (nmcli)..."
    if command_exists nmcli; then
        # Find the connection name for the interface
        CONNECTION_NAME=$(nmcli -g NAME,DEVICE connection show --active | awk -F: -v iface="$PRIMARY_INTERFACE" '$2 == iface {print $1}')
        if [[ -n "$CONNECTION_NAME" ]]; then
            print_status "Enabling Wake-on-LAN (magic packet) for $PRIMARY_INTERFACE via NetworkManager connection '$CONNECTION_NAME'..."
            sudo nmcli connection modify "$CONNECTION_NAME" 802-3-ethernet.wake-on-lan magic
            print_status "Wake-on-LAN enabled for $PRIMARY_INTERFACE (connection: $CONNECTION_NAME)"
            print_status "You may need to reactivate the connection or reboot for changes to take effect."
        else
            print_warning "Could not find an active NetworkManager connection for $PRIMARY_INTERFACE. Please configure WoL manually."
        fi
    else
        print_warning "NetworkManager (nmcli) not found. Please enable Wake-on-LAN manually for $PRIMARY_INTERFACE."
    fi
    
    print_status "Sleeper setup complete!"
    print_warning "Don't forget to:"
    print_warning "1. Configure the application in /etc/sleep-manager/"
    print_warning "2. Start the service with: systemctl start sleep-manager-sleeper"
}

# Function to setup waker machine
setup_waker() {
    print_status "Setting up WAKER machine..."
    
    # Create sleep-manager user and group
    print_status "Creating sleep-manager user and group..."
    if ! id "sleep-manager" &>/dev/null; then
        useradd --system --user-group --shell /bin/false --home-dir /usr/lib/sleep-manager sleep-manager
        print_status "Created sleep-manager user"
    else
        print_status "sleep-manager user already exists"
    fi
    
    # Create application directory
    print_status "Setting up application directory..."
    mkdir -p /usr/lib/sleep-manager
    
    # Copy project files, excluding development-specific directories
    print_status "Copying project files..."
    cd "$PROJECT_DIR"
    for item in *; do
        # Skip venv, .git, and other development directories
        if [[ "$item" != "venv" && "$item" != ".git" && "$item" != "debian" && "$item" != "__pycache__" && "$item" != "*.pyc" ]]; then
            if [[ -d "$item" ]]; then
                cp -r "$item" /usr/lib/sleep-manager/
            else
                cp "$item" /usr/lib/sleep-manager/
            fi
        fi
    done

    # Setup configuration directory
    print_status "Setting up configuration directory..."
    mkdir -p /etc/sleep-manager

    if [[ ! -f /etc/sleep-manager/sleep-manager-config.json ]]; then
        if [[ -f /usr/lib/sleep-manager/config/sleep-manager-config.json ]]; then
            cp /usr/lib/sleep-manager/config/sleep-manager-config.json /etc/sleep-manager/sleep-manager-config.json
            chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json
            chmod 0640 /etc/sleep-manager/sleep-manager-config.json
            print_status "Migrated existing config to /etc/sleep-manager/sleep-manager-config.json"
        elif [[ -f /usr/local/sleep-manager/config/sleep-manager-config.json ]]; then
            cp /usr/local/sleep-manager/config/sleep-manager-config.json /etc/sleep-manager/sleep-manager-config.json
            chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json
            chmod 0640 /etc/sleep-manager/sleep-manager-config.json
            print_status "Migrated existing config to /etc/sleep-manager/sleep-manager-config.json"
        fi
    fi

    # Copy example configuration file if it exists
    if [[ -f "$PROJECT_DIR/config/sleep-manager-config.json.example" ]]; then
        cp "$PROJECT_DIR/config/sleep-manager-config.json.example" /etc/sleep-manager/sleep-manager-config.json.example
        print_status "Copied example configuration file to /etc/sleep-manager/"
        print_warning "Please edit /etc/sleep-manager/sleep-manager-config.json.example and rename it to sleep-manager-config.json"
        chown root:sleep-manager /etc/sleep-manager/sleep-manager-config.json.example
        chmod 0644 /etc/sleep-manager/sleep-manager-config.json.example
    else
        print_warning "Example configuration file not found. Please create /etc/sleep-manager/sleep-manager-config.json manually."
    fi
    
    chown -R sleep-manager:sleep-manager /usr/lib/sleep-manager
    chmod 755 /usr/lib/sleep-manager
    
    # Create and configure virtual environment
    print_status "Setting up Python virtual environment..."
    if ! command_exists python3; then
        print_error "python3 not found. Please install Python 3 first."
        exit 1
    fi
    
    # Create virtual environment
    cd /usr/lib/sleep-manager
    python3 -m venv venv
    chown -R sleep-manager:sleep-manager venv
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install --upgrade pip
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install -e .
    
    print_status "Virtual environment setup complete"
    
    # Install Flask application service
    print_status "Installing Flask application service..."
    cp "$PROJECT_DIR/systemd/sleep-manager-waker.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable sleep-manager-waker.service
    print_status "Flask application service installed and enabled"
    
    # Install etherwake
    if ! command_exists etherwake; then
        print_status "Installing etherwake..."
        if command_exists apt-get; then
            apt-get update
            apt-get install -y etherwake
        elif command_exists yum; then
            yum install -y etherwake
        elif command_exists dnf; then
            dnf install -y etherwake
        else
            print_warning "Could not install etherwake automatically. Please install it manually."
        fi
    fi
    
    if command_exists etherwake; then
        print_status "etherwake found: $(which etherwake)"
    else
        print_warning "etherwake not found. Please install it manually."
    fi

    configure_sudoers "waker"
    
    print_status "Waker setup complete!"
    print_warning "Don't forget to:"
    print_warning "1. Configure the application in /etc/sleep-manager/"
    print_warning "2. Start the service with: systemctl start sleep-manager-waker"
}

# Function to update dependencies
update_dependencies() {
    print_status "Updating Python dependencies..."
    
    if [[ ! -d /usr/lib/sleep-manager/venv ]]; then
        print_error "Virtual environment not found. Please run setup first."
        exit 1
    fi
    
    cd /usr/lib/sleep-manager
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install --upgrade pip
    sudo -u sleep-manager /usr/lib/sleep-manager/venv/bin/pip install --upgrade -e .
    
    print_status "Dependencies updated successfully!"
}

# Function to uninstall sleeper components
uninstall_sleeper() {
    print_status "Uninstalling SLEEPER components..."
    
    # Stop and disable Flask application service
    if systemctl is-enabled sleep-manager-sleeper.service >/dev/null 2>&1; then
        print_status "Stopping and disabling Flask application service..."
        systemctl stop sleep-manager-sleeper.service
        systemctl disable sleep-manager-sleeper.service
    fi
    
    # Remove Flask application service file
    if [[ -f /etc/systemd/system/sleep-manager-sleeper.service ]]; then
        print_status "Removing Flask application service file..."
        rm /etc/systemd/system/sleep-manager-sleeper.service
        systemctl daemon-reload
    fi
    
    # Stop and disable systemd delay service
    if systemctl is-enabled sleep-manager-delay.service >/dev/null 2>&1; then
        print_status "Stopping and disabling systemd delay service..."
        systemctl stop sleep-manager-delay.service
        systemctl disable sleep-manager-delay.service
    fi
    
    # Remove systemd service file
    if [[ -f /etc/systemd/system/sleep-manager-delay.service ]]; then
        print_status "Removing systemd service file..."
        rm /etc/systemd/system/sleep-manager-delay.service
        systemctl daemon-reload
    fi
    
    # Remove nmcli Wake-on-LAN configurations
    print_status "Removing nmcli Wake-on-LAN configurations..."
    if command_exists nmcli; then
        # Find all active connections and disable WoL
        while IFS=: read -r connection_name device; do
            if [[ -n "$connection_name" && -n "$device" ]]; then
                # Check if this connection has WoL enabled
                wol_setting=$(nmcli -g 802-3-ethernet.wake-on-lan connection show "$connection_name" 2>/dev/null || echo "")
                if [[ "$wol_setting" == "magic" ]]; then
                    print_status "Disabling WoL for connection '$connection_name' (device: $device)..."
                    nmcli connection modify "$connection_name" 802-3-ethernet.wake-on-lan ignore
                fi
            fi
        done < <(nmcli -g NAME,DEVICE connection show --active 2>/dev/null || true)
        print_status "Wake-on-LAN configurations removed via nmcli"
    else
        print_warning "NetworkManager (nmcli) not found. WoL configurations may need manual removal."
    fi
    
    print_status "Sleeper uninstall complete!"
}

# Function to uninstall waker components
uninstall_waker() {
    print_status "Uninstalling WAKER components..."
    
    # Stop and disable Flask application service
    if systemctl is-enabled sleep-manager-waker.service >/dev/null 2>&1; then
        print_status "Stopping and disabling Flask application service..."
        systemctl stop sleep-manager-waker.service
        systemctl disable sleep-manager-waker.service
    fi
    
    # Remove Flask application service file
    if [[ -f /etc/systemd/system/sleep-manager-waker.service ]]; then
        print_status "Removing Flask application service file..."
        rm /etc/systemd/system/sleep-manager-waker.service
        systemctl daemon-reload
    fi
    
    print_status "Waker uninstall complete!"
}

# Function to uninstall all components
uninstall_all() {
    print_status "Uninstalling ALL components..."
    
    uninstall_sleeper
    uninstall_waker
    
    # Note: Application directory and virtual environment are preserved
    # This allows for easy reinstallation without losing configuration
    
    if id "sleep-manager" &>/dev/null; then
        print_status "Removing sleep-manager user..."
        userdel sleep-manager
    fi
    
    print_status "Complete uninstall finished!"
    print_warning "Application files in /usr/lib/sleep-manager have been preserved."
    print_warning "To reinstall, run the setup script again."
}

# Function to verify setup
verify_setup() {
    print_status "Verifying setup..."
    
    # Check systemctl (for sleeper)
    if command_exists systemctl; then
        print_status "✓ systemctl available"
        
        # Check if delay service is enabled
        if systemctl is-enabled sleep-manager-delay.service >/dev/null 2>&1; then
            print_status "✓ Systemd delay service enabled"
        else
            print_warning "✗ Systemd delay service not enabled"
        fi
    fi
    
    # Check etherwake (for waker)
    if command_exists etherwake; then
        print_status "✓ etherwake available"
    else
        print_warning "✗ etherwake not available"
    fi
    
    # Check ethtool (for sleeper)
    if ethtool_available >/dev/null 2>&1; then
        print_status "✓ ethtool available ($(ethtool_available))"
    else
        print_warning "✗ ethtool not available"
    fi
    
    # Check network connectivity
    print_status "Checking network connectivity..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_status "✓ Internet connectivity available"
    else
        print_warning "✗ No internet connectivity"
    fi
    
    # Check hostname resolution
    check_hostname_resolution || print_warning "Hostname resolution check failed or returned warnings"
}

# Function to show current status
show_status() {
    print_status "Current Sleep Manager Status"
    print_status "============================"
    
    # Check Flask application services
    if systemctl is-enabled sleep-manager-sleeper.service >/dev/null 2>&1; then
        print_status "✓ Sleep Manager Sleeper Service: ENABLED"
        if systemctl is-active sleep-manager-sleeper.service >/dev/null 2>&1; then
            print_status "  Status: ACTIVE"
        else
            print_warning "  Status: INACTIVE"
        fi
    elif systemctl is-enabled sleep-manager-waker.service >/dev/null 2>&1; then
        print_status "✓ Sleep Manager Waker Service: ENABLED"
        if systemctl is-active sleep-manager-waker.service >/dev/null 2>&1; then
            print_status "  Status: ACTIVE"
        else
            print_warning "  Status: INACTIVE"
        fi
    else
        print_warning "✗ Sleep Manager Flask Services: NOT ENABLED"
    fi
    
    # Check systemd delay service
    if systemctl is-enabled sleep-manager-delay.service >/dev/null 2>&1; then
        print_status "✓ Systemd delay service: ENABLED"
        if systemctl is-active sleep-manager-delay.service >/dev/null 2>&1; then
            print_status "  Status: ACTIVE"
        else
            print_warning "  Status: INACTIVE"
        fi
    else
        print_warning "✗ Systemd delay service: NOT ENABLED"
    fi
    
    # Check etherwake
    if command_exists etherwake; then
        print_status "✓ etherwake: INSTALLED ($(which etherwake))"
    else
        print_warning "✗ etherwake: NOT INSTALLED"
    fi
    
    # Check ethtool
    if ethtool_available >/dev/null 2>&1; then
        print_status "✓ ethtool: INSTALLED ($(ethtool_available))"
    else
        print_warning "✗ ethtool: NOT INSTALLED"
    fi
    
    # Check application directory
    if [[ -d /usr/lib/sleep-manager ]]; then
        print_status "✓ Application directory: INSTALLED (/usr/lib/sleep-manager)"
    else
        print_warning "✗ Application directory: NOT INSTALLED"
    fi
    
    # Check sleep-manager user
    if id "sleep-manager" &>/dev/null; then
        print_status "✓ sleep-manager user: EXISTS"
    else
        print_warning "✗ sleep-manager user: NOT EXISTS"
    fi

    # Check sudoers configuration
    if [[ -f /etc/sudoers.d/sleep-manager ]]; then
        sudoers_perms=$(stat -c "%a" /etc/sudoers.d/sleep-manager 2>/dev/null || echo "")
        sudoers_owner=$(stat -c "%U:%G" /etc/sudoers.d/sleep-manager 2>/dev/null || echo "")
        if [[ "$sudoers_perms" == "440" && "$sudoers_owner" == "root:root" ]]; then
            print_status "✓ sudoers file: /etc/sudoers.d/sleep-manager (0440 root:root)"
        else
            print_warning "✗ sudoers file permissions/owner invalid: /etc/sudoers.d/sleep-manager (${sudoers_perms:-unknown} ${sudoers_owner:-unknown})"
        fi

        if command_exists visudo; then
            if visudo -c -f /etc/sudoers.d/sleep-manager >/dev/null 2>&1; then
                print_status "✓ sudoers file syntax: OK"
            else
                print_warning "✗ sudoers file syntax: INVALID"
            fi
        fi
    else
        print_warning "✗ sudoers file: /etc/sudoers.d/sleep-manager NOT FOUND"
    fi
    
    # Check nmcli Wake-on-LAN configurations
    print_status "NetworkManager Wake-on-LAN configurations:"
    if command_exists nmcli; then
        wol_found=false
        while IFS=: read -r connection_name device; do
            if [[ -n "$connection_name" && -n "$device" ]]; then
                wol_setting=$(nmcli -g 802-3-ethernet.wake-on-lan connection show "$connection_name" 2>/dev/null || echo "")
                if [[ "$wol_setting" == "magic" ]]; then
                    print_status "✓ '$connection_name' ($device): WoL ENABLED"
                    wol_found=true
                elif [[ "$wol_setting" == "ignore" ]]; then
                    print_status "  '$connection_name' ($device): WoL DISABLED"
                else
                    print_status "  '$connection_name' ($device): WoL NOT SET"
                fi
            fi
        done < <(nmcli -g NAME,DEVICE connection show --active 2>/dev/null || true)
        
        if [[ "$wol_found" == "false" ]]; then
            print_warning "✗ No NetworkManager connections with WoL enabled found"
        fi
    else
        print_warning "✗ NetworkManager (nmcli) not found - cannot check WoL configurations"
    fi
    
    # Check hostname resolution
    echo
    check_hostname_resolution || print_warning "Hostname resolution check failed or returned warnings"
}

# Function to check Wake-on-LAN status using multiple methods
check_wol_status() {
    local interface="$1"
    local wol_status="Unknown"
    local ethtool_path

    ethtool_path=$(ethtool_available)
    if [[ -n "$ethtool_path" ]]; then
        wol_status=$("$ethtool_path" "$interface" 2>/dev/null | grep -i "Wake-on" | head -n1 || echo "")
        if [[ -n "$wol_status" ]]; then
            echo "$wol_status"
            return 0
        fi
    fi

    # Fallback: Check sysfs directly
    if [[ -f "/sys/class/net/$interface/device/power/wakeup" ]]; then
        local wakeup_value
        wakeup_value=$(cat "/sys/class/net/$interface/device/power/wakeup" 2>/dev/null || echo "unknown")
        if [[ "$wakeup_value" == "enabled" ]]; then
            echo "Wake-on: enabled (sysfs)"
            return 0
        elif [[ "$wakeup_value" == "disabled" ]]; then
            echo "Wake-on: disabled (sysfs)"
            return 0
        fi
    fi

    # Check if interface supports WoL at all
    if [[ -d "/sys/class/net/$interface/device" ]]; then
        if [[ -f "/sys/class/net/$interface/device/power/wakeup" ]] || \
           [[ -f "/sys/class/net/$interface/device/power/control" ]]; then
            echo "Wake-on: supported (power management available)"
            return 0
        else
            echo "Wake-on: not supported (no power management)"
            return 0
        fi
    fi

    echo "Wake-on: unknown status"
    return 0
}

# Function to check if ethtool is available with better path handling
ethtool_available() {
    # Check common locations
    local ethtool_paths=(
        "/usr/sbin/ethtool"
        "/usr/bin/ethtool"
        "/sbin/ethtool"
        "/bin/ethtool"
    )
    
    for path in "${ethtool_paths[@]}"; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    # Check PATH
    if command_exists ethtool; then
        which ethtool
        return 0
    fi
    
    return 1
}

# Main script
main() {
    print_warning "Legacy installer: prefer the .deb on Debian; use manual steps on other distros."
    print_warning "This script is best-effort and may not work on all non-Debian systems."
    # Check if no arguments provided
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    # Parse command line arguments
    case "$1" in
        sleeper)
            check_root
            detect_system
            print_status "Detected system: $OS $VER"
            setup_sleeper
            verify_setup
            echo
            print_status "Setup complete!"
            print_warning "Please review docs/installation.rst for additional manual configuration steps."
            print_warning "Don't forget to configure Wake-on-LAN in your BIOS/UEFI settings!"
            ;;
        waker)
            check_root
            detect_system
            print_status "Detected system: $OS $VER"
            setup_waker
            verify_setup
            echo
            print_status "Setup complete!"
            print_warning "Please review docs/installation.rst for additional manual configuration steps."
            ;;
        both)
            check_root
            detect_system
            print_status "Detected system: $OS $VER"
            setup_sleeper
            setup_waker
            verify_setup
            echo
            print_status "Setup complete!"
            print_warning "Please review docs/installation.rst for additional manual configuration steps."
            print_warning "Don't forget to configure Wake-on-LAN in your BIOS/UEFI settings!"
            ;;
        uninstall-sleeper)
            check_root
            uninstall_sleeper
            echo
            print_status "Uninstall complete!"
            ;;
        uninstall-waker)
            check_root
            uninstall_waker
            echo
            print_status "Uninstall complete!"
            ;;
        uninstall-all)
            check_root
            uninstall_all
            echo
            print_status "Uninstall complete!"
            ;;
        update-deps)
            check_root
            update_dependencies
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 
