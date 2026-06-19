#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/setup_scripts/common.sh"

VENV_DIR="$REPO_ROOT/venv"

source "$VENV_DIR/bin/activate"

log_info "Running final environment verification"

COMMANDS=(
    python3
    pip3
    tmux
    zmap
)

for cmd in "${COMMANDS[@]}"; do
    if ! check_command "$cmd"; then
        log_error "Verification failed for command: $cmd"
        exit 1
    fi

    log_success "$cmd verified"
done

python - <<EOF
import requests
from bs4 import BeautifulSoup
import pandas
import matplotlib
import numpy
import scapy

print("Final Python verification successful")
EOF

log_success "Environment verification completed"
