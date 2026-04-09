# Hardware Verkabelung - LEGO Sortiermaschine

## 📋 Übersicht aller Komponenten

| Komponente | Modell/Typ | Anzahl | Stromversorgung |
|------------|------------|--------|-----------------|
| Mikrocontroller | Raspberry Pi 3 | 1 | 5V 2.5A (USB) |
| Motor-Controller | L298N Dual H-Bridge | 1 | 12V 2A extern |
| Servo | 180°| 1 | 5V (von Raspi) |
| DC-Motor | Förderband-Motor 12V | 1 | über L298N |
| Sensor | IR Lichtschranke (digital) | 1 | 5V (von Raspi) |
| Netzteil | 12V 2-3A | 1 | 230V AC → 12V DC |
| Kamera | Android-Handy (DroidCam) | 1 | USB (von Raspi) |

---

## 🔌 GPIO Pin-Belegung Raspberry Pi 3

```
┌─────────────────────────────────────────┐
│         Raspberry Pi 3 GPIO             │
│                                         │
│    3.3V  [1]  [2]  5V                   │
│          [3]  [4]  5V                   │
│          [5]  [6]  GND  ← L298N GND     │
│          [7]  [8]                       │
│     GND  [9]  [10]                      │
│  SERVO [11] [12]                        │
│         [13] [14] GND                   │
│         [15] [16]                       │
│   3.3V [17] [18] GPIO 18 ← Servo PWM    │
│         [19] [20] GND                   │
│         [21] [22] GPIO 22 ← L298N IN1   │
│         [23] [24]                       │
│     GND [25] [26]                       │
│         [27] [28]                       │
│  SENSOR[29] [30] GND                    │
│         [31] [32] GPIO 27 ← L298N ENA   │
│         [33] [34] GND                   │
│         [35] [36] GPIO 23 ← L298N IN2   │
│         [37] [38]                       │
│     GND [39] [40]                       │
└─────────────────────────────────────────┘

Verwendete Pins:
├── GPIO 17  (Pin 11) → Lichtschranke (Digital Input)
├── GPIO 18  (Pin 12) → Servo PWM Signal
├── GPIO 22  (Pin 15) → L298N IN1 (Richtung)
├── GPIO 23  (Pin 16) → L298N IN2 (Richtung)
├── GPIO 27  (Pin 13) → L298N ENA (PWM Geschwindigkeit)
├── GND      (Pin 6)  → Gemeinsame Masse
└── 5V       (Pin 2)  → Servo Stromversorgung
```

---

## 🔧 Detaillierte Verkabelung

### 1️⃣ L298N Motor-Controller (Förderband)

```
┌──────────────────────────────────────────────────────────────┐
│                    L298N ANSCHLÜSSE                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CONTROL SIDE (Links):                                       │
│  ┌────────────────────────────────────┐                     │
│  │  ENA    ← GPIO 27 (Pin 13)         │ PWM Geschwindigkeit │
│  │  IN1    ← GPIO 22 (Pin 15)         │ Richtung           │
│  │  IN2    ← GPIO 23 (Pin 16)         │ Richtung           │
│  │  IN3    (nicht verwendet)          │                    │
│  │  IN4    (nicht verwendet)          │                    │
│  │  ENB    (nicht verwendet)          │                    │
│  └────────────────────────────────────┘                     │
│                                                              │
│  POWER SIDE (Rechts):                                        │
│  ┌────────────────────────────────────┐                     │
│  │  12V    ← Netzteil 12V (+)         │ Motorspannung      │
│  │  GND    ← Netzteil GND (-)         │ Motor-Masse        │
│  │  5V     (nicht anschließen!)       │ Optional Out       │
│  └────────────────────────────────────┘                     │
│                                                              │
│  MOTOR OUTPUTS (Mitte):                                      │
│  ┌────────────────────────────────────┐                     │
│  │  OUT1   ← DC-Motor (+)             │ Motor A            │
│  │  OUT2   ← DC-Motor (-)             │ Motor A            │
│  │  OUT3   (nicht verwendet)          │ Motor B            │
│  │  OUT4   (nicht verwendet)          │ Motor B            │
│  └────────────────────────────────────┘                     │
│                                                              │
│  LOGIC GROUND:                                               │
│  ┌────────────────────────────────────┐                     │
│  │  GND    ← Raspberry Pi GND (Pin 6) │ Gemeinsame Masse!  │
│  └────────────────────────────────────┘                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

⚠️ WICHTIGE JUMPER-EINSTELLUNGEN:

┌─────────────────────────────────┐
│  Jumper bei ENA:  [ENTFERNEN]  │  ← Für PWM-Kontrolle
│  Jumper bei 12V:  [ENTFERNEN]  │  ← Bei 12V Motoren
└─────────────────────────────────┘
```

**Verkabelungs-Schritte:**

```bash
1. Netzteil ausgeschaltet lassen!
2. L298N ENA Jumper entfernen
3. Raspberry Pi mit L298N verbinden:
   - GPIO 27 → ENA
   - GPIO 22 → IN1
   - GPIO 23 → IN2
   - GND (Pin 6) → GND (Logic Ground am L298N)

4. Motor mit L298N verbinden:
   - Motor Kabel 1 → OUT1
   - Motor Kabel 2 → OUT2
   - Polarität später testen (falls falsche Richtung: tauschen)

5. Netzteil mit L298N verbinden:
   - Netzteil (+) → 12V
   - Netzteil (-) → GND (Power)

6. Erdung: L298N GND mit Netzteil GND verbinden (oft schon intern)
```

---

### 2️⃣ Servo (Sortierweiche)

```
┌──────────────────────────────────────────────────────────────┐
│                 SERVO ANSCHLUSS (3 Kabel)                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Servo-Stecker (Standard 3-Pin):                             │
│                                                              │
│    ┌─────────────────────────────────┐                      │
│    │  BRAUN/SCHWARZ  → GND (Pin 6)   │  Masse              │
│    │  ROT            → 5V  (Pin 2)   │  Stromversorgung    │
│    │  ORANGE/GELB    → GPIO 18       │  PWM Signal         │
│    └─────────────────────────────────┘                      │
│                                                              │
│  Alternative Farben (je nach Hersteller):                    │
│  ├── Braun/Schwarz/Blau = GND                               │
│  ├── Rot              = 5V                                   │
│  └── Orange/Gelb/Weiß = Signal                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘

⚠️ WICHTIG: 
- Servo braucht stabiles 5V (min. 1A)
- Bei mehreren Servos: Externes 5V Netzteil empfohlen
- Raspberry Pi 5V Pin hat begrenzte Leistung (max. 1.2A total)
```

**Verkabelungs-Schritte:**

```bash
1. Servo-Stecker identifizieren (3 Kabel)
2. Kabel mit Raspberry Pi verbinden:
   - Braun/Schwarz → Pin 6 (GND)
   - Rot           → Pin 2 (5V)
   - Orange/Gelb   → Pin 12 (GPIO 18)

3. Optional: Servo extern versorgen (bei Stromproblermen):
   - 5V Netzteil (+) → Servo Rot
   - 5V Netzteil (-) → Servo Braun UND Raspi GND
   - Raspi GPIO 18   → Servo Signal
```

---

### 3️⃣ IR Lichtschranke (Digital)

```
┌──────────────────────────────────────────────────────────────┐
│              LICHTSCHRANKE (3 oder 4 Kabel)                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Standard Digital-Modul:                                     │
│                                                              │
│    ┌─────────────────────────────────┐                      │
│    │  VCC    → 5V  (Pin 2)           │  Stromversorgung    │
│    │  GND    → GND (Pin 6)           │  Masse              │
│    │  OUT/D0 → GPIO 17 (Pin 11)      │  Digital Signal     │
│    └─────────────────────────────────┘                      │
│                                                              │
│  Logik (je nach Modul):                                      │
│  ├── HIGH (3.3V) = Lichtweg frei                            │
│  └── LOW  (0V)   = Objekt erkannt                           │
│                                                              │
│  oder invertiert:                                            │
│  ├── LOW  (0V)   = Lichtweg frei                            │
│  └── HIGH (3.3V) = Objekt erkannt                           │
│                                                              │
│  → Im Code einstellbar: SENSOR_ACTIVE_LOW = True/False      │
│                                                              │
└──────────────────────────────────────────────────────────────┘

🔧 EINSTELLUNGEN AM SENSOR-MODUL:

Viele Module haben ein Potentiometer (blaue Schraube):
┌────────────────────────────────┐
│  ╭─────╮                       │
│  │  ⊕  │  ← Empfindlichkeit    │
│  │     │     (im Uhrzeigersinn │
│  ╰─────╯      = empfindlicher) │
└────────────────────────────────┘
```

**Verkabelungs-Schritte:**

```bash
1. Sensor-Modul identifizieren (meist 3 Pins)
2. Mit Raspberry Pi verbinden:
   - VCC → Pin 2 (5V)
   - GND → Pin 6 (GND)
   - OUT → Pin 11 (GPIO 17)

3. Sensor ausrichten:
   - TX (Sender) und RX (Empfänger) gegenüber
   - Abstand: 1-10cm (je nach Modul)
   - Über Förderband montieren

4. Empfindlichkeit testen:
   - Programm starten
   - Sensor-Test Modus wählen
   - Potentiometer drehen bis zuverlässige Erkennung
```

---

### 4️⃣ Android-Handy (DroidCam Kamera)

```
┌──────────────────────────────────────────────────────────────┐
│                   HANDY VERBINDUNG (USB)                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Raspberry Pi ──USB──► Android Handy                         │
│                                                              │
│  Kabel:                                                      │
│  ├── USB-A (Raspi) → USB-C/Micro-USB (Handy)                │
│  └── Daten + Stromversorgung                                 │
│                                                              │
│  Software:                                                   │
│  ├── Handy: DroidCam App installiert                         │
│  ├── Raspi: ADB installiert                                  │
│  └── Automatische Verbindung via Script                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Anforderungen:
- USB 2.0 Port am Raspberry Pi
- USB-Debugging am Handy aktiviert
- DroidCam App gestartet (USB-Modus)
```

---

## 🔋 Stromversorgung - Übersicht

```
┌────────────────────────────────────────────────────────────┐
│                  STROMVERSORGUNG                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  230V Steckdose                                            │
│       │                                                    │
│       ├──► Netzteil 1: 5V 2.5A (USB)                      │
│       │         │                                          │
│       │         └──► Raspberry Pi 3                        │
│       │                  │                                 │
│       │                  ├──► Servo (5V, max 1A)          │
│       │                  ├──► Lichtschranke (5V, ~20mA)   │
│       │                  └──► Android Handy (USB, ~500mA) │
│       │                                                    │
│       └──► Netzteil 2: 12V 2-3A                           │
│                 │                                          │
│                 └──► L298N Motor-Controller               │
│                          │                                 │
│                          └──► DC-Motor (12V, ~1-2A)       │
│                                                            │
└────────────────────────────────────────────────────────────┘

⚡ LEISTUNGSBEDARF:
├── Raspberry Pi 3:      ~2.5A @ 5V  = 12.5W
├── Servo:               ~1.0A @ 5V  = 5W
├── Lichtschranke:       ~0.02A @ 5V = 0.1W
├── Android Handy:       ~0.5A @ 5V  = 2.5W
├── DC-Motor:            ~2.0A @ 12V = 24W
└── GESAMT:                           ~44W

Empfohlene Netzteile:
├── Raspberry Pi: Original 5V 3A USB-Netzteil
└── L298N/Motor: 12V 3A Schaltnetzteil
```

---

## 🛠️ Verkabelungs-Checkliste

### Vor dem Einschalten:

```
☐ L298N Jumper entfernt (ENA)
☐ Alle GND-Verbindungen korrekt (gemeinsame Masse!)
☐ Keine Kurzschlüsse zwischen 5V und GND
☐ Keine Kurzschlüsse zwischen 12V und GND
☐ Motor-Kabel fest verschraubt
☐ Servo-Stecker richtig herum (Braun = GND)
☐ Lichtschranke TX/RX richtig ausgerichtet
☐ USB-Kabel für Handy angeschlossen
☐ Netzteile NOCH NICHT eingesteckt
```

### Beim ersten Einschalten:

```
1. Raspberry Pi Netzteil einstecken
   → Warten bis Boot abgeschlossen (grüne LED blinkt)

2. 12V Netzteil einstecken
   → L298N sollte NICHT heiß werden
   → Motor sollte NICHT drehen (PWM = 0%)

3. DroidCam App auf Handy starten
   → USB-Modus wählen
   → "Start" drücken

4. Programm starten:
   $ cd ~/lego_sorter
   $ ./start_gui.sh

5. Sensor-Test durchführen (Taste [3])
   → Hand durch Lichtschranke bewegen
   → Anzeige sollte wechseln: "frei" ↔ "TEIL"

6. Manuell-Modus testen (Taste [F2])
   → Band starten [B]
   → Band sollte drehen
   → Falls falsche Richtung: IN1/IN2 tauschen

7. Servo testen (Kalibrierung [K])
   → Servo sollte sich drehen
   → Sanft und kontrolliert (nicht ruckartig)
```

---

## 🐛 Fehlerbehebung

### Motor dreht nicht:

```
☐ L298N ENA Jumper entfernt?
☐ 12V Netzteil eingeschaltet?
☐ Motor-Kabel richtig angeschlossen (OUT1/OUT2)?
☐ GPIO 27 Verbindung korrekt?
☐ Im Code: belt_speed_percent > 0?
```

### Motor dreht falsch herum:

```
Lösung 1: Hardware (empfohlen)
  → Motor-Kabel tauschen: OUT1 ↔ OUT2

Lösung 2: Software
  → IN1/IN2 im Code invertieren
```

### Servo reagiert nicht:

```
☐ 5V Versorgung vorhanden? (Multimeter messen)
☐ GPIO 18 Verbindung korrekt?
☐ Servo-Kabel richtig herum? (Braun = GND)
☐ Servo defekt? (mit anderem PWM-Signal testen)
```

### Lichtschranke erkennt nicht:

```
☐ 5V Versorgung vorhanden?
☐ TX/RX richtig ausgerichtet (gegenüber)?
☐ Abstand zu groß? (näher zusammen)
☐ Empfindlichkeit verstellen (Potentiometer)
☐ SENSOR_ACTIVE_LOW im Code anpassen (True/False)
```

### Raspberry Pi startet nicht:

```
☐ Netzteil stark genug? (min. 2.5A)
☐ SD-Karte korrekt eingesteckt?
☐ Rote LED leuchtet? (ja = Stromversorgung OK)
☐ Grüne LED blinkt? (ja = Boot-Vorgang läuft)
```

### L298N wird heiß:

```
⚠️ SOFORT AUSSCHALTEN!

Ursachen:
☐ 12V Jumper noch drin? → Entfernen!
☐ Motor zieht zu viel Strom? → Kleineren Motor verwenden
☐ Kurzschluss? → Verkabelung prüfen
☐ Motor blockiert? → Mechanik prüfen
```

---

## 📸 Kamera-Position

```
                    KAMERA-MONTAGE
                    
              ┌─────────────────┐
              │   Handy-Halter  │
              │                 │
              │   ┌─────────┐   │
              │   │  Handy  │   │
              │   │         │   │
              │   │ ┌─────┐ │   │ ← Kamera nach unten
              │   │ │  ◉  │ │   │
              │   │ └─────┘ │   │
              │   └─────────┘   │
              └────────┬────────┘
                       │
              Höhe: 15-20cm
                       │
                       ▼
              ═════════════════════
              FÖRDERBAND (mit Teil)
              ═════════════════════

Beleuchtung:
  💡 ← LED Links     LED Rechts → 💡
  
Ausrichtung:
- Kamera mittig über Förderband
- Senkrecht nach unten (90°)
- Fokus auf Förderband-Oberfläche
- Gleichmäßige Ausleuchtung
```

---

## 🎯 Optimale Positionen

### Lichtschranke:

```
Position auf Förderband:
├── 10-15cm VOR der Kamera
├── Höhe: Knapp über Förderband (5-10mm)
└── Sender/Empfänger: Seitlich am Band

Warum?
→ Teil wird erkannt
→ Band stoppt
→ Teil rutscht in Kamera-Position
→ Perfekte Zentrierung!
```

### Sortierweiche (Servo):

```
Position:
├── NACH der Kamera (15-20cm)
├── Rampe über Behälter-Reihe
└── Servo dreht Rampe zu Behältern

 Abstand
```

---

## ✅ Finale Checkliste

```
MECHANIK:
☐ Förderband läuft flüssig
☐ Servo dreht frei (kein Blockieren)
☐ Behälter richtig positioniert
☐ Kamera fest montiert
☐ Beleuchtung gleichmäßig

ELEKTRONIK:
☐ Alle Kabel fest verbunden
☐ Keine lockeren Stecker
☐ Gemeinsame Masse (GND) verbunden
☐ Jumper korrekt gesetzt/entfernt
☐ Netzteile richtig dimensioniert

SOFTWARE:
☐ Programm startet ohne Fehler
☐ Kamera-Verbindung funktioniert
☐ Sensor reagiert zuverlässig
☐ Servo-Positionen kalibriert
☐ Inventar wird gespeichert

SICHERHEIT:
☐ Keine blanken Kabel
☐ Netzteil mit Überlastschutz
☐ Not-Aus möglich (Stecker ziehen)
☐ L298N überhitzt nicht
☐ Keine Quetschgefahr am Band
```

---

## 💻 Software – Schnellstart

Die vollständige Steuerungssoftware befindet sich im Verzeichnis `lego_sorter/`.

### Erstinstallation

```bash
cd ~/LegoLAS_Kimpfler/lego_sorter
bash setup.sh
```

### GUI starten

```bash
./start_gui.sh
```

### GUI im Entwicklungsmodus (ohne Vollbild)

```bash
python3 main.py --no-fullscreen
```

### DroidCam-Kamera verwenden

```bash
python3 main.py --droidcam
```

### Autostart einrichten (Raspberry Pi Desktop)

```bash
mkdir -p ~/.config/autostart
cp ~/LegoLAS_Kimpfler/lego_sorter/legolas.desktop ~/.config/autostart/
```

### Tastaturkürzel (Übersicht)

| Taste     | Funktion                          |
|-----------|-----------------------------------|
| F2        | Sortier-Ansicht öffnen            |
| F3        | Kalibrierungs-Ansicht öffnen      |
| F4        | Einstellungs-Ansicht öffnen       |
| F5        | Datenbank-Ansicht öffnen          |
| B         | Förderband an/aus                 |
| Leertaste | Manuell scannen                   |
| A         | Automatik-Modus an/aus            |
| 1–6       | Sortierweiche auf Behälter X stellen |
| Escape    | Anwendung beenden                 |

Weitere Details zur Software-Architektur: [Software.md](Software.md)

