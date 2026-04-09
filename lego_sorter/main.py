"""
LegoLAS – Einstiegspunkt.

Starte mit:
    python3 main.py

Optionen:
    --no-fullscreen    Fenster statt Vollbild (nützlich für Entwicklung)
    --mock-gpio        Erzwingt Mock-GPIO auch auf einem Pi
    --log-level LEVEL  Logging-Level (DEBUG, INFO, WARNING, ERROR)

Kamera: DroidCam via USB (ADB Port-Forward auf tcp:4747).
Vor dem Start sicherstellen, dass die DroidCam-App läuft und das
Handy per USB verbunden ist. Das start_gui.sh-Script erledigt dies
automatisch.
"""

import argparse
import logging
import os
import sys

# Sicherstellen, dass das Paket-Verzeichnis im Pfad liegt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    parser = argparse.ArgumentParser(
        description="LegoLAS – LEGO Sortiermaschine Steuerung")
    parser.add_argument("--no-fullscreen", action="store_true",
                        help="Startet im Fenstermodus statt Vollbild")
    parser.add_argument("--log-level",
                        default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging-Level")
    return parser.parse_args()


def setup_logging(level_str: str):
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    args = parse_args()
    setup_logging(args.log_level)

    import config as cfg  # noqa: F401  (Monkey-Patching der Konfiguration)

    from gui.app import LegoLASApp

    app = LegoLASApp()

    if args.no_fullscreen:
        app.attributes("-fullscreen", False)
        app.geometry("1280x800")

    app.mainloop()


if __name__ == "__main__":
    main()
