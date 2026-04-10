# 🧱 LegoLAS – LEGO Sortiermaschine

**LegoLAS** ist eine automatische LEGO-Sortiermaschine, die auf dem **Raspberry Pi 3** läuft. Ein Förderband transportiert LEGO-Teile an einer Kamera vorbei. Die [Brickognize-API](https://api.brickognize.com/docs) erkennt die Teile, und eine Servo-gesteuerte Weiche sortiert sie in bis zu 6 Behälter.

Als Kamera wird ausschließlich ein **Android-Handy mit der DroidCam-App** per WLAN (lokales Netzwerk) verwendet.

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
- Handy und Raspberry Pi im selben lokalen WLAN

### 2. Einmaliges Setup

```bash
cd ~/LegoLAS_Kimpfler/lego_sorter
bash setup.sh
```

Das Script installiert alle Systempakete (`python3-tk` usw.)
und legt eine virtuelle Python-Umgebung mit allen Abhängigkeiten an.

### 3. DroidCam verbinden

```
# Am Handy: DroidCam-App öffnen → WLAN-Modus → START drücken
# Die angezeigte IP-Adresse notieren (z. B. 192.168.1.100)
```

Anschließend die IP-Adresse in `config.py` eintragen:

```python
DROIDCAM_URL = "http://<Handy-IP>:4747/video"
```

Alternativ kann die URL auch im Einstellungs-Menü der GUI (F4) angepasst werden.

### 4. Anwendung starten

```bash
./start_gui.sh
```

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

## ⚡ Performance auf Raspberry Pi 3

Die Anwendung ist für den Raspberry Pi 3 optimiert:

- **Kamera-Preview standardmäßig deaktiviert**: Statt eines Live-Bildes wird in der GUI nur ein leichter Status-Text angezeigt (Kamera online/offline, Frame-Zähler, Lag-Warnung). Das spart erheblich CPU und verhindert GUI-Ruckeln.
- **Stream-Lag minimiert**: Der Kamera-Capture-Thread liest Frames so schnell wie möglich und hält den internen OpenCV-Puffer leer, sodass beim Scannen immer ein aktueller Frame vorliegt (kein 10-Sekunden-Lag mehr).
- **Non-Blocking GUI**: Manueller Scan und automatischer Sortierbetrieb laufen in eigenen Threads – der Tkinter-Main-Thread bleibt immer reaktionsfähig.

### Kamera-Preview aktivieren

Falls ein Live-Kamerabild gewünscht wird (z. B. auf stärkerer Hardware), kann die Preview in `lego_sorter/config.py` aktiviert werden:

```python
GUI_SHOW_CAMERA_PREVIEW = True   # Standard: False
```

---



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
