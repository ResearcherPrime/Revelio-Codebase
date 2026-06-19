#!/usr/bin/env bash

set -e
set -u

log_info() {
    echo "[*] $1"
}

log_success() {
    echo "[+] $1"
}

log_error() {
    echo "[ERROR] $1"
}

check_command() {
    local cmd="$1"

    if command -v "$cmd" >/dev/null 2>&1; then
        return 0
    fi

    return 1
}

install_apt_package() {
    local pkg="$1"

    if dpkg -s "$pkg" >/dev/null 2>&1; then
        log_success "$pkg already installed"
        return
    fi

    log_info "Installing package: $pkg"

    if [[ $EUID -ne 0 ]]; then
        sudo apt-get install -y "$pkg"
    else
        apt-get install -y "$pkg"
    fi

    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        log_error "Failed to install package: $pkg"
        log_error "Please install manually and rerun setup"
        exit 1
    fi

    log_success "$pkg installation verified"
}
