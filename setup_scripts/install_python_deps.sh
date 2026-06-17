#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/setup_scripts/common.sh"

VENV_DIR="$REPO_ROOT/venv"

log_info "Creating Python virtual environment"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

log_info "Installing Python dependencies"

pip install --upgrade pip
pip install -r "$REPO_ROOT/requirements.txt"

log_info "Verifying Python imports"

python - <<EOF
import requests
from bs4 import BeautifulSoup
import pandas
import matplotlib
import numpy
import scapy

print("Python dependency verification successful")
EOF

log_success "Python dependencies verified"
