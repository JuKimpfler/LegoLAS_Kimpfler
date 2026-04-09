# 🧱 LegoLAS – LEGO Sortiermaschine

**LegoLAS** ist eine automatische LEGO-Sortiermaschine, die auf dem **Raspberry Pi 3** läuft. Ein Förderband transportiert LEGO-Teile an einer Kamera vorbei. Die [Brickognize-API](https://api.brickognize.com/docs) erkennt die Teile, und eine Servo-gesteuerte Weiche sortiert sie in bis zu 6 Behälter.

Als Kamera wird ausschließlich ein **Android-Handy mit der DroidCam-App** per USB verwendet.

---

## 📦 Komponenten

| Komponente       | Modell/Typ                    | Anzahl |
|------------------|-------------------------------|--------|
| Mikrocontroller  | Raspberry Pi 3                | 1      |
| Motor-Controller | L298N Dual H-Bridge           | 1      |
| Servo            | 180°-Servo                    | 1      |
| DC-Motor         | Förderband-Motor 12V          | 1      |
| Sensor           | IR-Lichtschranke (digital)    | 1      |
| Netzteil         | 12V 2–3A                      | 1      |
| Kamera           | Android-Handy mit DroidCam    | 1      |

---

## 🚀 Schnellstart

### 1. Voraussetzungen

- Raspberry Pi 3 mit Raspberry Pi OS (Bullseye oder neuer)
- Android-Handy mit installierter [DroidCam-App](https://www.dev47apps.com/) (Play Store)
- USB-Kabel (Handy ↔ Raspberry Pi)

### 2. Einmaliges Setup

```bash
cd ~/LegoLAS_Kimpfler/lego_sorter
bash setup.sh
```

Das Script installiert alle Systempakete (`adb`, `python3-tk`, `ffmpeg` usw.)
und legt eine virtuelle Python-Umgebung mit allen Abhängigkeiten an.

### 3. DroidCam verbinden

```bash
# Am Handy: DroidCam-App öffnen → USB-Modus → START drücken
# USB-Debugging am Handy erlauben (Popup bestätigen)

# Verbindung prüfen
adb devices              # Zeigt: "XXXXXXX   device"
adb forward tcp:4747 tcp:4747
```

### 4. Anwendung starten

```bash
./start_gui.sh
```

Das Script richtet die ADB Port-Weiterleitung automatisch ein und startet die GUI.

### 5. Entwicklung (ohne Vollbild)

```bash
python3 main.py --no-fullscreen
```

---

## 🔌 GPIO-Verkabelung (Raspberry Pi 3, BCM-Nummerierung)

| GPIO | Pin | Funktion               |
|------|-----|------------------------|
| 17   | 11  | IR-Lichtschranke Input |
| 18   | 12  | Servo PWM Signal       |
| 22   | 15  | L298N IN1 (Richtung)   |
| 23   | 16  | L298N IN2 (Richtung)   |
| 27   | 13  | L298N ENA (PWM Speed)  |
| GND  | 6   | Gemeinsame Masse       |
| 5V   | 2   | Servo Stromversorgung  |

Detaillierte Verkabelungspläne → [Hardware.md](Hardware.md)

---

## ⌨️ Tastaturkürzel

| Taste     | Funktion                      |
|-----------|-------------------------------|
| F2        | Sortier-Ansicht               |
| F3        | Kalibrierungs-Ansicht         |
| F4        | Einstellungs-Ansicht          |
| F5        | Datenbank-Ansicht             |
| B         | Förderband an/aus             |
| Leertaste | Manuell scannen               |
| A         | Automatik-Modus an/aus        |
| 1–6       | Weiche auf Behälter X stellen |
| Escape    | Anwendung beenden             |

---

## 📁 Projektstruktur

```
lego_sorter/
├── main.py            # Einstiegspunkt
├── config.py          # GPIO-Pins, Kamera-URL, Standardwerte
├── requirements.txt   # Python-Abhängigkeiten
├── setup.sh           # Einmaliges System-Setup
├── start_gui.sh       # Anwendung starten (mit DroidCam-Setup)
├── legolas.desktop    # Autostart-Eintrag für LXDE/Pixel Desktop
│
├── hardware/
│   ├── gpio_controller.py   # Motor, Servo, Sensor
│   └── camera_manager.py    # DroidCam via OpenCV/HTTP-Stream
│
├── core/
│   ├── brickognize.py       # Brickognize REST-API Client
│   ├── database.py          # SQLite (Inventar, Log, Aufträge)
│   ├── order_manager.py     # Excel-Import/Export
│   └── sorter_engine.py     # Sortier-Zustandsmaschine
│
└── gui/
    ├── base.py              # Theme, BaseView
    ├── app.py               # Hauptfenster
    ├── sort_view.py         # Sortier-Menü (Live-Kamera, Steuerung)
    ├── calibration_view.py  # Kalibrierungs-Menü (Servo-Positionen)
    ├── settings_view.py     # Einstellungs-Menü
    └── database_view.py     # Datenbank-Menü
```

---

## 📖 Weitere Dokumentation

- [Software.md](Software.md) – Software-Architektur, GUI-Module, Zustandsmaschine
- [Hardware.md](Hardware.md) – Detaillierte Verkabelung und mechanischer Aufbau
- [Features.md](Features.md) – Feature-Übersicht
