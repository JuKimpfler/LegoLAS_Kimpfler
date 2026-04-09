# LegoLAS – Feature-Übersicht

Vollständige Beschreibung aller implementierten Funktionen auf Basis des aktuellen Quellcodes.

---

## 1. GUI (Hauptanwendung)

### Allgemein
- Tkinter-basierte Oberfläche, startet im **Vollbild-Modus** (`--no-fullscreen` für Entwicklung)
- **Dunkles Theme** (Catppuccin-Farbpalette: Hintergrund `#1e1e2e`, Oberfläche `#313244`, Akzent `#89b4fa` u. a.)
- **Toolbar** oben mit Logo, Tab-Buttons, Notfall-STOP-Button und Beenden-Button
- **Notfall-STOP** stoppt sofort Motor und Engine
- **Beenden** mit Bestätigungsdialog; räumt Hardware-Ressourcen auf
- Vier Views, die per Toolbar-Tab oder Tastenkürzel umgeschaltet werden

---

## 2. Sortier-Ansicht (F2)

### Live-Kameravorschau
- Anzeige des DroidCam-Streams in Echtzeit (Standard: **8 FPS**, konfigurierbar)
- Skaliert automatisch auf die verfügbare Fenstergröße
- Zeigt Platzhaltertext, wenn Kamera nicht verbunden

### Status-Panel
- **Zustand**: IDLE / Warte auf Teil / Band stoppt / Scanne / Sortiere / Band läuft / FEHLER / PAUSIERT
- **Letztes Teil**: Teilenummer, Name und Konfidenz des zuletzt erkannten Teils
- **Behälter**: Ziel-Behälter des zuletzt sortierten Teils
- **Sensor**: Echtzeit-Statusanzeige der IR-Lichtschranke (◉ TEIL ERKANNT / ○ frei)

### Betriebs- und Modusauswahl
- Umschalten zwischen **Manuell** und **Automatik** (Radiobutton / Taste `A`)
- Umschalten zwischen **Sortiermodus** und **Auftragsmodus** (Radiobutton)
- **Auftragsauswahl** per Dropdown (Combobox); Liste wird live aus der Datenbank geladen

### Manuelle Steuerung
- **Band starten / stoppen** (Button + Taste `B`)
- **Manuell scannen** (Button + Taste `Space`): Einzelscan ohne automatischen Loop
- **Weiche stellen** (Buttons 1–6 + Tasten `1`–`6`): Servo direkt auf gespeicherte Behälterposition fahren

---

## 3. Kalibrierungs-Ansicht (F3)

- **Live-Winkelanzeige** des aktuellen Servo-Winkels in Grad
- **Grob-Schritte** ±10° per Button
- **Fein-Schritte** ±1° per Button
- **Direkte Eingabe** per Slider (0–180°)
- **Slots 1–6 speichern**: Aktuelle Position als Behälter-Slot in der Datenbank ablegen
- **Tabellenansicht** aller gespeicherten Slot-Winkel (Treeview)
- **Zu gespeichertem Slot fahren**: Ausgewählten Slot aus der Tabelle anfahren
- **Startposition (0°)**: Servo auf Home-Position zurückfahren

---

## 4. Einstellungs-Ansicht (F4)

Drei Tabs:

### Tab „Allgemein"
- **Bandgeschwindigkeit** per Slider (10–100 %) – wirkt sofort auf den laufenden Motor
- **Erkennungsschwelle** (Konfidenz-Threshold) per Slider (10–100 %) – Mindest-Konfidenz für gültige Identifikation (Standard: 70 %)
- **DroidCam URL** (Textfeld, Standard: `http://localhost:4747/video`)
- **Behälter-Beschriftungen**: Freitext-Name für jeden der 6 Behälter
- **Einstellungen speichern**: Persistiert alle Werte in der SQLite-Datenbank

### Tab „Auftragslisten"
- **Excel-Import** (`.xlsx` / `.xls`): Lädt eine Auftragsliste und legt einen neuen Auftrag in der Datenbank an
  - Spaltenformat: A = Teilenummer, B = Name, C = Anzahl, D = Behälter (1–6)
  - Kopfzeile wird automatisch erkannt und übersprungen
- **Auftragsübersicht** als Tabelle (ID, Name, Erstellt, Abgeschlossen ✅)
- **Auftrag löschen** (mit Bestätigung)

### Tab „Export"
- **Inventar als Excel exportieren** (`inventar.xlsx`)
- **Auftrag als Excel exportieren** (Spalten: Teilenummer, Name, Behälter, Soll, Ist, Offen)
- **Fehlende Teile exportieren** (nur offene Positionen, sortiert nach Behälter)
- **Datenbank exportieren** (`.db`-Datei kopieren)
- **Datenbank importieren** (vorhandene Datenbank überschreiben, mit Warnung)

---

## 5. Datenbank-Ansicht (F5)

Vier Tabs:

### Tab „Statistik"
- Gesamtzahl aller gescannten Teile (großes Zahl-Label)
- Fortschrittsbalken und Stückzahl je Behälter (1–6)

### Tab „Auftragsfortschritt"
- Auftragsauswahl per Dropdown
- Fortschrittsbalken (Prozent) und Ist/Soll-Anzeige je Behälter für den gewählten Auftrag

### Tab „Inventar"
- Vollständige Inventartabelle: Teilenummer, Name, Behälter, Anzahl, Letzte Aktualisierung
- Vertikale und horizontale Scrollleisten

### Tab „Scan-Log"
- Log der letzten 200 Scans: Zeitstempel, Teilenummer, Name, Konfidenz, Behälter
- Neueste Einträge zuerst

### Allgemeine Aktionen
- **Inventar zurücksetzen** (mit Bestätigung; löscht alle Inventar-Einträge)
- **Daten aktualisieren** (alle Tabs neu laden)

---

## 6. Globale Tastenkürzel

| Taste     | Funktion                                 |
|-----------|------------------------------------------|
| `F2`      | Sortier-Ansicht öffnen                   |
| `F3`      | Kalibrierungs-Ansicht öffnen             |
| `F4`      | Einstellungs-Ansicht öffnen              |
| `F5`      | Datenbank-Ansicht öffnen                 |
| `Escape`  | Anwendung beenden (mit Bestätigung)      |
| `B`       | Förderband an/aus (in Sortier-Ansicht)   |
| `Space`   | Manuell scannen (in Sortier-Ansicht)     |
| `A`       | Automatik-Modus an/aus                   |
| `1`–`6`   | Weiche auf Behälter 1–6 stellen          |

---

## 7. Automatischer Sortierbetrieb (SorterEngine)

### Zustandsmaschine
```
IDLE → WAITING_FOR_PART → STOPPING_BELT → SCANNING → SORTING → BELT_RESTART → IDLE
```

### Sortiermodus
- Teile werden nach Typ erkannt und im Inventar erfasst
- Bekannte Teile werden in den bereits verwendeten Behälter einsortiert
- Neue (unbekannte) Teile kommen in Behälter 1

### Auftragsmodus
- Teile werden gemäß dem aktiven Auftrag sortiert
- Behälter 1 hat höchste Priorität (wird zuerst befüllt)
- Auftragsfortschritt (fulfilled/required) wird je Teil fortgeschrieben
- Auftrag wird automatisch als abgeschlossen markiert, wenn alle Positionen erfüllt sind

### Fallback
- Teile, die nicht mit ausreichender Konfidenz erkannt werden, landen in **Behälter 6**

### Weitere Funktionen
- **Pause / Resume** des automatischen Loops
- **Manueller Scan** ohne laufenden Loop (für Einzel-Tests)
- Thread-sicherer Betrieb (Sortier-Loop in eigenem Daemon-Thread)

---

## 8. Hardware-Integration

### Förderband (DC-Motor, L298N-Treiber)
- **Start** mit konfigurierbarer Geschwindigkeit (0–100 % PWM)
- **Stop**
- **Rückwärtsfahrt**
- GPIO-Pins (BCM): IN1 = 22, IN2 = 23, ENA = 27 (PWM-Frequenz: 100 Hz)
- Kurze Pause vor dem Scan (`BELT_STOP_DELAY = 0,3 s`)

### Servo (Sortierweiche)
- 6 kalibrierbare Positionen (Behälter-Slots 1–6), in Datenbank gespeichert
- Winkelbereich 0–180°, PWM-Frequenz 50 Hz
- GPIO-Pin (BCM): 18
- Standardpositionen: Slot 1 = 10°, 2 = 46°, 3 = 82°, 4 = 118°, 5 = 154°, 6 = 175°
- Home-Position: 0°
- PWM wird nach der Bewegung deaktiviert, um Servo-Zittern zu verhindern

### IR-Lichtschranke
- GPIO-Pin (BCM): 17, Pull-Up, Active-Low
- Polling im Sortier-Loop und Echtzeit-Anzeige in der GUI

### Mock-Modus
- Wenn `RPi.GPIO` nicht verfügbar ist, wird automatisch ein **Software-Mock** aktiviert
- Kamera-Dummy erzeugt graue Platzhalter-Frames mit Statustext
- Ermöglicht GUI-Betrieb und Tests ohne Raspberry Pi und angeschlossene Hardware

---

## 9. Kamera (DroidCam)

- Ausschließlich **DroidCam via USB** (ADB Port-Forward auf `tcp:4747`)
- URL: `http://localhost:4747/video` (konfigurierbar)
- Auflösung: 640 × 480 Pixel
- Kontinuierlicher Capture-Loop in eigenem Thread (thread-sicher)
- Frame-Bereitstellung als BGR-Array (OpenCV) und als PIL-Image (für tkinter)
- JPEG-Kodierung für Brickognize-API-Upload (Qualität 90 %)
- Fallback-Dummy wenn DroidCam nicht verbunden oder OpenCV fehlt

---

## 10. KI-Teilerkennung (Brickognize API)

- REST-API: `https://api.brickognize.com/predict/`
- Upload des aktuellen Frames als JPEG (`multipart/form-data`)
- Rückgabe: Liste von Treffern mit Teilenummer, Name, Konfidenz-Score
- **Best-Match**: Bestes Ergebnis über dem Konfidenz-Schwellenwert (Standard: 0,7)
- Timeout: 10 Sekunden
- Graceful Degradation: Bei API-Fehler oder `requests`-Fehlen → Fallback-Behälter 6

---

## 11. Datenbank (SQLite)

Datei: `lego_sorter/data/legolas.db`

### Tabellen

| Tabelle       | Inhalt                                                                 |
|---------------|------------------------------------------------------------------------|
| `inventory`   | Teilenummer, Name, Behälter, Anzahl, Zeitstempel (UNIQUE pro Teil+Behälter) |
| `scan_log`    | Zeitstempel, Teilenummer, Name, Konfidenz, Behälter, Auftrags-ID       |
| `orders`      | Auftrags-ID, Name, Erstellt, Abgeschlossen                             |
| `order_items` | Auftrag-ID, Teilenummer, Behälter, Soll (required), Ist (fulfilled)    |
| `servo_cal`   | Slot (1–6), Winkel in Grad                                             |
| `settings`    | Schlüssel-Wert-Paare (JSON-kodiert)                                    |

### Besonderheiten
- WAL-Modus und Foreign-Keys aktiviert
- `inventory`: Konflikt-Resolution per `UPSERT` (Anzahl wird addiert)
- `servo_cal`: Standardwerte werden beim ersten Start automatisch eingetragen
- `settings`: Persistiert Bandgeschwindigkeit, Konfidenz-Schwelle, DroidCam-URL und Behälter-Namen
- Inventar-Import möglich (Zeilen-Dictionary)

---

## 12. Auftragsmanagement (Excel, openpyxl)

### Import
- Dateiformat: `.xlsx` / `.xls`
- Spalten: A = Teilenummer, B = Name, C = Anzahl, D = Behälter (1–6)
- Kopfzeilen werden automatisch erkannt (`teilenummer`, `part_num`, `part`, `id`)
- Behälternummer wird auf 1–6 begrenzt; fehlende Werte → Behälter 6, Anzahl 1

### Export
- **Auftragsliste**: Spalten Teilenummer, Name, Behälter, Soll, Ist, Offen
- **Fehlende Teile**: Nur offene Positionen, sortiert nach Behälter
- **Inventar**: Teilenummer, Name, Behälter, Anzahl, Zuletzt aktualisiert
- Alle Exporte: Kopfzeile farblich hervorgehoben (dunkelblau), abwechselnde Zeilenfarben, automatische Spaltenbreite

---

## 13. Systemintegration

- **Autostart** via `lego_sorter/legolas.desktop` (XDG-Desktop-Eintrag)
- **Startskript** `lego_sorter/start_gui.sh`: Führt `adb forward tcp:4747 tcp:4747` aus und startet danach die GUI
- **Setup-Skript** `lego_sorter/setup.sh`: Installiert Abhängigkeiten
- **Logging**: Konfigurierbares Level (`--log-level DEBUG/INFO/WARNING/ERROR`), Format mit Zeitstempel und Logger-Name
- **Startparameter**:
  - `--no-fullscreen`: Startet im Fenstermodus (1280 × 800) statt Vollbild
  - `--log-level LEVEL`: Setzt den Logging-Level
- **Dateiverzeichnisse** werden beim Start automatisch angelegt:
  - `lego_sorter/data/` – Datenbank und Einstellungen
  - `lego_sorter/data/orders/` – Importierte Auftragsdateien
  - `lego_sorter/data/exports/` – Exportierte Excel- und DB-Dateien

