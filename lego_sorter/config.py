"""
LegoLAS – Zentrale Konfiguration
Alle Hardware-Pins, Standardwerte und Pfade werden hier definiert.
"""

import os

# ---------------------------------------------------------------------------
# GPIO-Pin-Belegung (BCM-Nummerierung)
# ---------------------------------------------------------------------------
PIN_SENSOR      = 17   # IR-Lichtschranke (Eingang)
PIN_SERVO       = 18   # Servo PWM
PIN_MOTOR_IN1   = 22   # L298N IN1  (Richtung)
PIN_MOTOR_IN2   = 23   # L298N IN2  (Richtung)
PIN_MOTOR_ENA   = 27   # L298N ENA  (PWM-Geschwindigkeit)

# Lichtschranke: True = Signal LOW wenn Teil erkannt
SENSOR_ACTIVE_LOW = True

# ---------------------------------------------------------------------------
# Servo-Kalibrierung
# ---------------------------------------------------------------------------
SERVO_MIN_DUTY   = 2.5    # Duty-Cycle für 0°
SERVO_MAX_DUTY   = 12.5   # Duty-Cycle für 180°
SERVO_FREQ       = 50     # PWM-Frequenz in Hz

# Servo-Positionen für 6 Behälter (Grad, werden in DB gespeichert)
DEFAULT_SERVO_POSITIONS = {
    1: 10,
    2: 46,
    3: 82,
    4: 118,
    5: 154,
    6: 175,
}

# Position für "Warte-Stellung" (kein Behälter)
SERVO_HOME_ANGLE = 0

# ---------------------------------------------------------------------------
# Motor / Förderband
# ---------------------------------------------------------------------------
MOTOR_PWM_FREQ       = 100   # Hz
DEFAULT_BELT_SPEED   = 60    # Prozent (0-100)
BELT_STOP_DELAY      = 0.3   # Sekunden – Band hält kurz an vor dem Scan

# ---------------------------------------------------------------------------
# Kamera (DroidCam via USB – einzige unterstützte Kameraquelle)
# ---------------------------------------------------------------------------
# DroidCam läuft auf dem Android-Handy und streamt via USB (ADB Port-Forward)
DROIDCAM_URL         = "http://localhost:4747/video"
CAMERA_WIDTH         = 640
CAMERA_HEIGHT        = 480
LIVE_FPS             = 8     # FPS für Live-Vorschau in der GUI

# ---------------------------------------------------------------------------
# Brickognize API
# ---------------------------------------------------------------------------
BRICKOGNIZE_URL      = "https://api.brickognize.com/predict/"
API_TIMEOUT          = 10    # Sekunden
DEFAULT_CONF_THRESHOLD = 0.7  # Mindest-Konfidenz für Identifikation

# ---------------------------------------------------------------------------
# Pfade & Dateien
# ---------------------------------------------------------------------------
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
DATA_DIR         = os.path.join(BASE_DIR, "data")
DB_PATH          = os.path.join(DATA_DIR, "legolas.db")
SETTINGS_PATH    = os.path.join(DATA_DIR, "settings.json")
ORDERS_DIR       = os.path.join(DATA_DIR, "orders")
EXPORTS_DIR      = os.path.join(DATA_DIR, "exports")

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
WINDOW_TITLE     = "LegoLAS – LEGO Sortiermaschine"
THEME_BG         = "#1e1e2e"
THEME_SURFACE    = "#313244"
THEME_ACCENT     = "#89b4fa"
THEME_ACCENT2    = "#a6e3a1"
THEME_DANGER     = "#f38ba8"
THEME_TEXT       = "#cdd6f4"
THEME_MUTED      = "#585b70"
FONT_MONO        = ("Courier New", 10)
FONT_BODY        = ("Helvetica", 11)
FONT_TITLE       = ("Helvetica", 16, "bold")

# Tastatur-Bindings
KEY_TOGGLE_BELT  = "b"
KEY_SCAN         = "space"
KEY_AUTO_TOGGLE  = "a"
KEY_MANUAL       = "F2"
KEY_CALIBRATE    = "F3"
KEY_SETTINGS     = "F4"
KEY_DATABASE     = "F5"
KEY_QUIT         = "Escape"
