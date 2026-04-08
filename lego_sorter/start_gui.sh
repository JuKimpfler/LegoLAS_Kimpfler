#!/usr/bin/env bash
# =============================================================================
# LegoLAS – GUI starten
# Wird beim Autostart des Raspberry Pi automatisch aufgerufen.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"

# Display setzen (für Autostart ohne Desktop-Session)
export DISPLAY="${DISPLAY:-:0}"

# Virtuelle Umgebung aktivieren (falls vorhanden)
if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
fi

# DroidCam-Verbindung herstellen (optional – nur wenn ADB verfügbar)
if command -v adb &>/dev/null; then
    adb start-server 2>/dev/null || true
    if adb devices 2>/dev/null | grep -q "device$"; then
        echo "[LegoLAS] Android-Gerät gefunden – richte Port-Weiterleitung ein"
        adb forward tcp:4747 tcp:4747 2>/dev/null || true
    fi
fi

# Anwendung starten
cd "$SCRIPT_DIR"
exec python3 main.py "$@"
