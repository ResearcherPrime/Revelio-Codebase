#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/setup_scripts/common.sh"

log_info "Installing system dependencies"

if [[ $EUID -ne 0 ]]; then
    sudo apt-get update
else
    apt-get update
fi

SYSTEM_PACKAGES=(
    python3
    python3-pip
    python3-venv
    tmux
    build-essential
    cmake
    libgmp3-dev
    gengetopt
    libpcap-dev
    flex
    byacc
    libjson-c-dev
    pkg-config
    libunistring-dev
    libjudy-dev
    unzip
)

for pkg in "${SYSTEM_PACKAGES[@]}"; do
    install_apt_package "$pkg"
done

REQUIRED_COMMANDS=(
    python3
    pip3
    tmux
    gcc
    make
    cmake
    unzip
)

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! check_command "$cmd"; then
        log_error "Required command missing after installation: $cmd"
        log_error "Please install manually"
        exit 1
    fi

    log_success "Verified command: $cmd"
done

log_success "System dependency installation completed"
