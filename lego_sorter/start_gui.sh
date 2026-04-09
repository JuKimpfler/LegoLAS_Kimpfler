#!/usr/bin/env bash
# =============================================================================
# LegoLAS – GUI starten
# Wird beim Autostart des Raspberry Pi automatisch aufgerufen.
#
# Voraussetzung: Android-Handy mit DroidCam-App per USB angeschlossen
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

# DroidCam-Verbindung herstellen (Pflicht)
if command -v adb &>/dev/null; then
    echo "[LegoLAS] Starte ADB-Server..."
    adb start-server 2>/dev/null || true

    echo "[LegoLAS] Warte auf Android-Gerät..."
    if adb wait-for-device 2>/dev/null; then
        echo "[LegoLAS] Android-Gerät gefunden:"
        adb devices -l 2>/dev/null || true
        echo "[LegoLAS] Richte DroidCam Port-Weiterleitung ein (tcp:4747)..."
        adb forward tcp:4747 tcp:4747 2>/dev/null || \
            echo "[LegoLAS] WARNUNG: Port-Weiterleitung fehlgeschlagen!"
    else
        echo "[LegoLAS] WARNUNG: Kein Android-Gerät gefunden!"
        echo "[LegoLAS] Bitte Handy per USB verbinden und USB-Debugging erlauben."
        echo "[LegoLAS] Starte trotzdem – Kamera zeigt Platzhalter-Bild."
    fi
else
    echo "[LegoLAS] WARNUNG: 'adb' nicht gefunden!"
    echo "[LegoLAS] Bitte 'sudo apt install adb' ausführen."
fi

echo "[LegoLAS] Starte Anwendung..."

# Anwendung starten
cd "$SCRIPT_DIR"
exec python3 main.py "$@"
