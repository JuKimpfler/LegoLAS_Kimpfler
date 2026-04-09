#!/usr/bin/env bash
# =============================================================================
# LegoLAS – Einmaliges System-Setup für Raspberry Pi
# Ausführen mit:  bash setup.sh
# =============================================================================

set -euo pipefail

echo "========================================"
echo "  LegoLAS System-Setup"
echo "========================================"

# --- System aktualisieren ---
sudo apt update

# --- Systempakete ---
sudo apt install -y \
    python3-full \
    python3-pip \
    python3-venv \
    python3-tk

# --- Virtuelle Python-Umgebung ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
# RPi.GPIO nur auf echtem Pi installieren
if python3 -c "import platform; assert 'aarch64' in platform.machine() or 'arm' in platform.machine()" 2>/dev/null; then
    pip install RPi.GPIO pigpio
fi
deactivate

echo ""
echo "========================================"
echo "  Setup abgeschlossen!"
echo "  Starte die Anwendung mit:  ./start_gui.sh"
echo "========================================"
