#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

source "$REPO_ROOT/setup_scripts/common.sh"

log_info "Starting artifact setup"

bash "$REPO_ROOT/setup_scripts/install_system_deps.sh"
bash "$REPO_ROOT/setup_scripts/install_python_deps.sh"
bash "$REPO_ROOT/setup_scripts/build_zmap.sh"
bash "$REPO_ROOT/setup_scripts/verify_environment.sh"

log_success "Artifact setup completed successfully"
