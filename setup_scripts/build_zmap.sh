#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/setup_scripts/common.sh"

ZIP_FILE="$REPO_ROOT/external/zstun.zip"
EXTRACT_DIR="$REPO_ROOT/external"
ZSTUN_DIR="$EXTRACT_DIR/zmap-4.3.4"
BUILD_DIR="$ZSTUN_DIR/build"

log_info "Building Zstun"

if [[ ! -f "$ZIP_FILE" ]]; then
    log_error "Missing file: $ZIP_FILE"
    exit 1
fi

cd "$EXTRACT_DIR"

if [[ ! -d "$ZSTUN_DIR" ]]; then
    unzip "$ZIP_FILE"
fi

cd "$ZSTUN_DIR"

rm -rf build
mkdir build
cd build

cmake .. -DCMAKE_INSTALL_PREFIX=/usr
make -j$(nproc)

if [[ $EUID -ne 0 ]]; then
    sudo make install
else
    make install
fi

if ! check_command zmap; then
    log_error "Zstun installation failed"
    log_error "Please manually build/install Zstun"
    exit 1
fi

zmap --version

log_success "Zstun build verified"
