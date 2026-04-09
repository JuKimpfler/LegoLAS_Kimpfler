# LegoLAS – Software-Dokumentation

## Übersicht

Die Steuerungssoftware läuft vollständig auf dem **Raspberry Pi 3** und ist in Python 3 geschrieben. Sie übernimmt:

- Hardwaresteuerung (Förderband, Servo-Weiche, IR-Lichtschranke)
- Kameraanbindung via **DroidCam** (Android-Handy als WLAN-Kamera)
- LEGO-Teilerkennung via [Brickognize-API](https://api.brickognize.com/docs)
- Vollbild-GUI (tkinter, modernes dunkles Design)
- Datenbankverwaltung (SQLite)
- Auftrags- und Inventarverwaltung (Excel-basiert)
- Automatischer Betrieb per Lichtschranke

---

## Projektstruktur

```
lego_sorter/
├── main.py                    # Einstiegspunkt
├── config.py                  # GPIO-Pins, DroidCam-URL, Standardwerte, Theme
├── requirements.txt           # Python-Abhängigkeiten
├── setup.sh                   # Einmaliges System-Setup
├── start_gui.sh               # Anwendung starten (mit DroidCam-Setup)
├── legolas.desktop            # Autostart-Eintrag für LXDE/Pixel Desktop
│
├── hardware/
│   ├── gpio_controller.py     # RPi.GPIO-Abstraktion (Motor, Servo, Sensor)
│   └── camera_manager.py      # DroidCam via OpenCV HTTP-Stream
│
├── core/
│   ├── brickognize.py         # Brickognize REST-API Client
│   ├── database.py            # SQLite-Datenbank (Inventar, Log, Aufträge)
│   ├── order_manager.py       # Excel-Import/Export für Auftragslisten
│   └── sorter_engine.py       # Sortier-Zustandsmaschine (Auto/Manuell)
│
└── gui/
    ├── base.py                # Theme, BaseView-Klasse
    ├── app.py                 # Hauptfenster (LegoLASApp)
    ├── sort_view.py           # Sortier-Menü (Live-Kamera, Steuerung)
    ├── calibration_view.py    # Kalibrierungs-Menü (Servo-Positionen)
    ├── settings_view.py       # Einstellungs-Menü (Speed, Threshold, Excel)
    └── database_view.py       # Datenbank-Menü (Statistik, Inventar, Log)
```

---

## Abhängigkeiten

| Paket           | Zweck                             | Installation                |
|----------------|-----------------------------------|-----------------------------|
| `requests`      | Brickognize HTTP-API              | `pip install requests`      |
| `opencv-python` | DroidCam-Stream via HTTP/OpenCV   | `pip install opencv-python` |
| `Pillow`        | Frame → tkinter ImageTk           | `pip install Pillow`        |
| `numpy`         | Frame-Datentypen                  | `pip install numpy`         |
| `openpyxl`      | Excel-Import/Export               | `pip install openpyxl`      |
| `RPi.GPIO`      | GPIO (**nur Raspberry Pi**)       | `pip install RPi.GPIO`      |
| `tkinter`       | GUI                               | `sudo apt install python3-tk` |

**Hinweis:** Auf Nicht-Raspberry-Pi-Systemen läuft die Anwendung mit einem Software-Mock für GPIO – nützlich für Entwicklung und Tests. Ohne DroidCam-Verbindung wird ein Platzhalter-Bild angezeigt.

---

## Kamera-Setup: DroidCam via WLAN

### Funktionsprinzip

Das Android-Handy streamt sein Kamerabild über das lokale WLAN an den Raspberry Pi.
OpenCV liest den Stream direkt als HTTP-URL (`http://<Handy-IP>:4747/video`).
Ein USB-Kabel oder ADB wird **nicht** benötigt.

```
┌──────────────┐    WLAN     ┌──────────────────────────────┐
│   Android    │◄───────────▶│      Raspberry Pi            │
│  + DroidCam  │             │  OpenCV → http://<IP>:4747/video │
└──────────────┘             └──────────────────────────────┘
```

### Vorteile
- ✅ Keine zusätzliche Kamera-Hardware nötig
- ✅ Kein USB-Kabel erforderlich
- ✅ Handy kann frei positioniert werden
- ✅ Einfaches Setup über lokales Netzwerk

### Schritt 1: DroidCam-App installieren

```
Play Store → „DroidCam" suchen → installieren
Entwickler: Dev47Apps
Mindestversion: Android 5.0
```

### Schritt 2: Verbindung herstellen

```
# Handy und Raspberry Pi in dasselbe WLAN einbuchen
# DroidCam-App öffnen → WLAN-Modus → START drücken
# Die angezeigte IP-Adresse (z. B. 192.168.1.100) notieren
```

### Schritt 3: IP-Adresse konfigurieren

```python
# In config.py die IP-Adresse des Handys eintragen:
DROIDCAM_URL  = "http://<Handy-IP>:4747/video"
```

Alternativ kann die URL im Einstellungs-Menü der GUI (F4) angepasst werden.

### Schritt 4: Verbindung testen (optional)

Den Stream im Browser öffnen: `http://<Handy-IP>:4747/video`

### Konfiguration in config.py

```python
DROIDCAM_URL  = "http://<Handy-IP>:4747/video"   # Handy-IP eintragen
CAMERA_WIDTH  = 640
CAMERA_HEIGHT = 480
LIVE_FPS      = 8
```

Die URL kann im Einstellungs-Menü der GUI geändert werden.

---

## GUI-Module im Detail

### Sortier-Menü (F2)

Das Hauptmenü enthält:
- **Live-Kameravorschau** (links) mit konfigurierbaren FPS
- **Status-Panel** (Maschinenstand, letztes Teil, Zielbehälter, Sensor-Status)
- **Betriebsart:** Manuell ↔ Automatik
- **Modus:** Sortiermodus (Inventar aufbauen) ↔ Auftragsmodus (Excel-Liste abarbeiten)
- **Auftragsliste:** Dropdown zur Auswahl des aktiven Auftrags
- **Schnellauswahl Behälter 1–6** (Weiche manuell stellen)

### Kalibrierungs-Menü (F3)

- Grob/Fein-Schritte (+/– 10° und +/– 1°)
- Direkteingabe via Slider (0°–180°)
- Slot 1–6 speichern (aktuelle Position für Behälter sichern)
- Tabelle aller gespeicherten Servo-Positionen

### Einstellungs-Menü (F4)

- Bandgeschwindigkeit (10–100%)
- Erkennungsschwelle / Konfidenz-Threshold (10–100%)
- DroidCam-URL (Standard: `http://192.168.1.100:4747/video`)
- Behälter-Beschriftungen
- Excel-Auftragsliste importieren / Aufträge verwalten
- Export: Inventar, Auftrag, fehlende Teile, Datenbank

### Datenbank-Menü (F5)

- Gesamtstatistik (Teile je Behälter)
- Auftragsfortschritt (Fortschrittsbalken je Behälter)
- Inventartabelle (Teilenummer, Name, Behälter, Anzahl)
- Scan-Log (chronologisch mit Konfidenz)

---

## Sortier-Zustandsmaschine

```
IDLE → WAITING_FOR_PART → STOPPING_BELT → SCANNING → SORTING → BELT_RESTART → WAITING_FOR_PART
```

Nicht erkannte Teile (Score < Schwellwert) → automatisch Behälter 6.

---

## Auftragslisten (Excel)

Spalten: **Teilenummer | Name | Anzahl | Behälter (1–6)**

Prioritätsregel: Behälter 1 zuerst, Behälter 6 = Aussortierschublade.

---

## Tastaturkürzel

| Taste     | Funktion                             |
|-----------|--------------------------------------|
| F2        | Sortier-Ansicht                      |
| F3        | Kalibrierung                         |
| F4        | Einstellungen                        |
| F5        | Datenbank                            |
| B         | Förderband an/aus                    |
| Leertaste | Manuell scannen                      |
| A         | Automatik-Modus an/aus               |
| 1–6       | Weiche auf Behälter X                |
| Escape    | Anwendung beenden                    |

---

## Schnellstart

```bash
# Einmaliges Setup
cd ~/LegoLAS_Kimpfler/lego_sorter
bash setup.sh

# DroidCam-App auf dem Handy starten (WLAN-Modus)
# IP-Adresse in config.py eintragen

# Starten
./start_gui.sh

# Entwicklung (ohne Vollbild)
python3 main.py --no-fullscreen
```

---

## Fehlerbehebung

| Problem                          | Lösung                                             |
|----------------------------------|----------------------------------------------------|
| Kamera zeigt „DroidCam nicht verbunden" | IP-Adresse in config.py oder den Einstellungen prüfen |
| Falsches Bild / kein Stream      | DroidCam-App neu starten, dann URL erneut testen   |
| Handy und Pi nicht erreichbar    | Beide Geräte ins selbe WLAN einbuchen              |
| Unscharfe Bilder                 | In DroidCam-App Autofokus aktivieren               |
| Langsame Verbindung              | WLAN-Signal verbessern oder Handy näher an Router  |
