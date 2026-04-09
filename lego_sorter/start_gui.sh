#!/usr/bin/env bash
# =============================================================================
# LegoLAS – GUI starten
# Wird beim Autostart des Raspberry Pi automatisch aufgerufen.
#
# Voraussetzung: Android-Handy mit DroidCam-App im selben lokalen Netzwerk (WLAN)
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

echo "[LegoLAS] Starte Anwendung..."
echo "[LegoLAS] Sicherstellen: DroidCam-App auf dem Handy läuft und Handy"
echo "[LegoLAS] ist im selben WLAN wie der Raspberry Pi."
echo "[LegoLAS] IP-Adresse in config.py bzw. in den Einstellungen prüfen."

# Anwendung starten
cd "$SCRIPT_DIR"
exec python3 main.py "$@"
