zur lego teil wrkennung wird https://brickognize.com/ verwendet. bzw. die api dieser webseite. 
https://api.brickognize.com/docs

# Option A: Android als USB-Webcam (DroidCam)

## Übersicht

DroidCam macht dein Android-Handy zu einer vollwertigen USB-Webcam, die der Raspberry Pi wie eine normale Kamera erkennt.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USB-WEBCAM MODUS                               │
│                                                                     │
│  ┌──────────────┐       USB        ┌──────────────────────────────┐│
│  │   Android    │◄────────────────▶│      Raspberry Pi            ││
│  │   + DroidCam │                  │      + DroidCam Client       ││
│  │              │                  │                              ││
│  │  Erscheint als:                 │  Erkennt als:                ││
│  │  "USB Webcam"                   │  /dev/video0                 ││
│  │                                 │                              ││
│  └──────────────┘                  └──────────────────────────────┘│
│                                                                     │
│  Vorteile:                                                         │
│  ✅ Schnell (~50ms Latenz)                                         │
│  ✅ Stabil                                                         │
│  ✅ Kein WiFi nötig                                                │
│  ✅ Handy wird gleichzeitig geladen                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Schritt 1: Android-App installieren

### DroidCam (Empfohlen)

```
Play Store → "DroidCam" suchen
Entwickler: Dev47Apps
Größe: ~5 MB
Mindestversion: Android 5.0

Alternative falls Play Store nicht geht:
→ APK von https://www.dev47apps.com/ herunterladen
→ "Unbekannte Quellen" aktivieren
→ APK installieren
```

### Nach Installation - App einrichten

```
┌─────────────────────────────────────┐
│         DroidCam                    │
├─────────────────────────────────────┤
│                                     │
│  WiFi IP: 192.168.1.xxx             │
│  Port: 4747                         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │                             │   │
│  │      [ Kamera-Vorschau ]    │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
│  Verbindungsmodus:                  │
│  ○ WiFi                             │
│  ● USB  ← Diese Option wählen!     │
│                                     │
│  [  START  ]                        │
│                                     │
└─────────────────────────────────────┘
```

---

## Schritt 2: Raspberry Pi einrichten

### Benötigte Pakete installieren

```bash
#!/bin/bash
# setup_droidcam.sh

echo "=== DroidCam USB Setup für Raspberry Pi ==="

# System aktualisieren
sudo apt update

# Grundlegende Pakete
sudo apt install -y \
    adb \
    v4l2loopback-dkms \
    v4l2loopback-utils \
    v4l-utils \
    ffmpeg \
    python3-opencv \
    python3-pip

# Python-Bibliotheken
pip3 install \
    requests \
    numpy \
    opencv-python \
    pillow

# V4L2 Loopback Modul laden (virtuelle Webcam)
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="DroidCam" exclusive_caps=1

# Modul beim Boot automatisch laden
echo "v4l2loopback" | sudo tee -a /etc/modules
echo 'options v4l2loopback devices=1 video_nr=10 card_label="DroidCam" exclusive_caps=1' | sudo tee /etc/modprobe.d/v4l2loopback.conf

# ADB-Regeln für USB
sudo tee /etc/udev/rules.d/51-android.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="*", MODE="0666", GROUP="plugdev"
EOF

sudo udevadm control --reload-rules

echo "Setup abgeschlossen!"
echo "Bitte Raspberry Pi neu starten: sudo reboot"
```

### Nach Neustart testen

```bash
# Prüfen ob v4l2loopback geladen
lsmod | grep v4l2loopback

# Verfügbare Video-Geräte anzeigen
v4l2-ctl --list-devices

# Sollte zeigen:
# DroidCam (platform:v4l2loopback-000):
#         /dev/video10
```

---

## Schritt 3: USB-Verbindung herstellen

### Verbindungsscript

```bash
#!/bin/bash
# connect_droidcam.sh

echo "=== DroidCam USB Verbindung ==="

# ADB-Server starten
adb start-server

# Auf Gerät warten
echo "Warte auf Android-Gerät..."
adb wait-for-device

# Gerät anzeigen
echo "Verbundenes Gerät:"
adb devices -l

# Port-Weiterleitung einrichten
echo "Richte Port-Weiterleitung ein..."
adb forward tcp:4747 tcp:4747

# Video-Stream starten
echo "Starte Video-Stream..."
echo "Öffne DroidCam App und drücke START!"
echo ""
echo "Stream wird auf /dev/video10 verfügbar sein"
echo "Drücke Strg+C zum Beenden"

# FFmpeg zum Empfangen des Streams und Weiterleiten an v4l2loopback
ffmpeg -i http://localhost:4747/video \
       -vf "format=yuv420p" \
       -f v4l2 \
       /dev/video10
```

### Manuell Schritt für Schritt

```bash
# 1. Handy per USB anschließen

# 2. USB-Debugging am Handy erlauben (Popup bestätigen)

# 3. ADB-Verbindung prüfen
adb devices
# Sollte zeigen: XXXXXXX    device

# 4. Port-Weiterleitung
adb forward tcp:4747 tcp:4747

# 5. DroidCam App öffnen → USB → START drücken

# 6. Stream testen
ffplay http://localhost:4747/video

# 7. An virtuelle Webcam weiterleiten (für OpenCV)
ffmpeg -i http://localhost:4747/video -f v4l2 /dev/video10
```

---

## Schritt 4: Python Lego-Scanner

### Vollständiges Script 

siehe python datei

## Schnellstart-Zusammenfassung

```
┌────────────────────────────────────────────────────────────────────┐
│                     SCHNELLSTART                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. HANDY:                                                         │
│     • DroidCam aus Play Store installieren                         │
│     • USB-Debugging aktivieren                                     │
│                                                                    │
│  2. RASPBERRY PI:                                                  │
│     $ sudo apt install adb python3-opencv                          │
│     $ pip3 install requests numpy                                  │
│                                                                    │
│  3. VERBINDEN:                                                     │
│     • USB-Kabel anschließen                                        │
│     • USB-Debugging erlauben (Popup am Handy)                      │
│     $ adb devices                                                  │
│     $ adb forward tcp:4747 tcp:4747                                │
│                                                                    │
│  4. STARTEN:                                                       │
│     • DroidCam App → USB → Start                                   │
│     $ python3 lego_scanner.py                                      │
│                                                                    │
│  5. SCANNEN:                                                       │
│     • Leertaste drücken = Foto + Analyse                           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Problemlösungen

| Problem | Lösung |
|---------|--------|
| DroidCam zeigt "Waiting for connection" | `adb forward tcp:4747 tcp:4747` ausführen |
| "No video stream" | DroidCam App neu starten |
| Unscharfe Bilder | 'F' drücken für Autofokus |
| Langsame Verbindung | USB 2.0 Port verwenden |
| OpenCV findet Kamera nicht | `http://localhost:4747/video` als URL verwenden |

Soll ich noch Details zur Halterung des Handys über dem Förderband oder zur Beleuchtung hinzufügen?