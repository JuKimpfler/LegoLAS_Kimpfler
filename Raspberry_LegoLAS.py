#!/usr/bin/env python3
"""
LEGO SORTIERMASCHINE
====================

Hardware-Konfiguration:
- GPIO 27: Förderband + Vibrationsmotor (gemeinsam an/aus)
- GPIO 18: Servo (0-180°, 6 Behälter)
- GPIO 17: Lichtschranke (digital: HIGH=frei, LOW=Teil erkannt)

Ablauf:
1. Band läuft
2. Teil erkannt (GPIO 17 = LOW)
3. Band stoppt
4. Kamera analysiert
5. Servo sortiert
6. Band läuft weiter
"""

import cv2
import requests
import numpy as np
import time
import subprocess
from threading import Thread, Lock
from datetime import datetime

# ══════════════════════════════════════════════════════════════
#                    KONFIGURATION
# ══════════════════════════════════════════════════════════════

# DroidCam
DROIDCAM_URL = "http://192.168.178.59:4747"

# Brickognize API
BRICKOGNIZE_URL = "https://api.brickognize.com/predict/"

# GPIO Pins
PIN_BELT_VIBRATOR = 27    # Förderband + Vibrationsmotor (gemeinsam)
PIN_SERVO = 18            # Sortier-Servo
PIN_SENSOR = 17           # Lichtschranke (digital)

# Sensor-Logik (anpassen falls invertiert!)
# True  = LOW bedeutet Teil erkannt
# False = HIGH bedeutet Teil erkannt
SENSOR_ACTIVE_LOW = True

# Servo-Positionen für 6 Behälter (0-180° gleichmäßig verteilt)
SERVO_ANGLES = [0, 36, 72, 108, 144, 180]

# Kategorien zu Behältern zuordnen
CATEGORY_TO_BIN = {
    "bricks":   0,    # Behälter 1 (0°)
    "plates":   1,    # Behälter 2 (36°)
    "tiles":    2,    # Behälter 3 (72°)
    "slopes":   3,    # Behälter 4 (108°)
    "technic":  4,    # Behälter 5 (144°)
    "unknown":  5,    # Behälter 6 (180°)
}

# Timing
SCAN_DELAY = 0.3          # Sekunden warten nach Stopp
SORT_DELAY = 0.5          # Sekunden für Servo-Bewegung
BELT_RESTART_DELAY = 0.3  # Sekunden bevor Band wieder startet
DEBOUNCE_TIME = 0.05      # Entprell-Zeit für Sensor

# Anzeige
PREVIEW_SCALE = 0.6       # Vorschau-Größe (60%)
PREVIEW_FPS = 15          # Maximale Vorschau-Framerate


# ══════════════════════════════════════════════════════════════
#                    GPIO & HARDWARE
# ══════════════════════════════════════════════════════════════

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("⚠ GPIO nicht verfügbar - Simulation aktiv")


class Hardware:
    """Hardware-Steuerung für Sortiermaschine"""
    
    def __init__(self):
        self.enabled = HAS_GPIO
        self.servo_pwm = None
        self.belt_running = False
        
        # Statistik
        self.stats = {cat: 0 for cat in CATEGORY_TO_BIN.keys()}
        self.total_parts = 0
        self.start_time = time.time()
        
        if self.enabled:
            self._setup_gpio()
    
    def _setup_gpio(self):
        """GPIO initialisieren"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Lichtschranke (Input mit Pull-Up)
        GPIO.setup(PIN_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Förderband + Vibrator (Output)
        GPIO.setup(PIN_BELT_VIBRATOR, GPIO.OUT)
        GPIO.output(PIN_BELT_VIBRATOR, GPIO.LOW)
        
        # Servo (PWM)
        GPIO.setup(PIN_SERVO, GPIO.OUT)
        self.servo_pwm = GPIO.PWM(PIN_SERVO, 50)  # 50 Hz
        self.servo_pwm.start(0)
        
        print("✓ GPIO initialisiert")
        print(f"  - Sensor an GPIO {PIN_SENSOR} (aktiv {'LOW' if SENSOR_ACTIVE_LOW else 'HIGH'})")
        print(f"  - Band/Vibrator an GPIO {PIN_BELT_VIBRATOR}")
        print(f"  - Servo an GPIO {PIN_SERVO}")
    
    def is_part_detected(self) -> bool:
        """
        Prüft ob Teil in Lichtschranke
        Returns: True wenn Teil erkannt
        """
        if not self.enabled:
            return False
        
        sensor_state = GPIO.input(PIN_SENSOR)
        
        if SENSOR_ACTIVE_LOW:
            return sensor_state == GPIO.LOW
        else:
            return sensor_state == GPIO.HIGH
    
    def wait_for_part(self, timeout: float = None) -> bool:
        """
        Wartet auf Teil-Erkennung mit Entprellung
        Returns: True wenn Teil erkannt, False bei Timeout
        """
        start_time = time.time()
        
        while True:
            if self.is_part_detected():
                # Entprellen: kurz warten und nochmal prüfen
                time.sleep(DEBOUNCE_TIME)
                if self.is_part_detected():
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.01)
    
    def belt_start(self):
        """Förderband + Vibrator starten"""
        if self.enabled:
            GPIO.output(PIN_BELT_VIBRATOR, GPIO.HIGH)
        self.belt_running = True
        print("▶ Band: AN")
    
    def belt_stop(self):
        """Förderband + Vibrator stoppen"""
        if self.enabled:
            GPIO.output(PIN_BELT_VIBRATOR, GPIO.LOW)
        self.belt_running = False
        print("■ Band: AUS")
    
    def set_servo_angle(self, angle: int):
        """Servo auf Winkel setzen (0-180°)"""
        angle = max(0, min(180, angle))
        
        if self.enabled and self.servo_pwm:
            # PWM Duty Cycle: 2.5% = 0°, 12.5% = 180°
            duty = 2.5 + (angle / 180.0) * 10.0
            self.servo_pwm.ChangeDutyCycle(duty)
            time.sleep(SORT_DELAY)
            self.servo_pwm.ChangeDutyCycle(0)
        else:
            print(f"[SIM] Servo → {angle}°")
            time.sleep(SORT_DELAY)
    
    def sort_to_bin(self, bin_number: int):
        """Teil in Behälter sortieren (0-5)"""
        bin_number = max(0, min(5, bin_number))
        angle = SERVO_ANGLES[bin_number]
        
        print(f"↳ Sortiere zu Behälter {bin_number + 1} (Winkel: {angle}°)")
        self.set_servo_angle(angle)
    
    def sort_to_category(self, category: str):
        """Teil nach Kategorie sortieren"""
        bin_number = CATEGORY_TO_BIN.get(category, 5)
        self.sort_to_bin(bin_number)
        
        # Statistik
        self.stats[category] = self.stats.get(category, 0) + 1
        self.total_parts += 1
    
    def get_sensor_status(self) -> str:
        """Sensor-Status als Text"""
        if not self.enabled:
            return "---"
        return "TEIL" if self.is_part_detected() else "frei"
    
    def print_stats(self):
        """Statistik im Terminal ausgeben"""
        elapsed = time.time() - self.start_time
        elapsed_min = elapsed / 60
        
        print("\n" + "═" * 60)
        print("                    SORTIER-STATISTIK")
        print("═" * 60)
        print(f"  Laufzeit:     {elapsed_min:.1f} Minuten")
        print(f"  Gesamt:       {self.total_parts} Teile")
        if elapsed_min > 0 and self.total_parts > 0:
            print(f"  Tempo:        {self.total_parts / elapsed_min:.1f} Teile/Minute")
        print("─" * 60)
        
        for category, count in sorted(self.stats.items(), key=lambda x: -x[1]):
            if count > 0:
                pct = (count / self.total_parts * 100) if self.total_parts > 0 else 0
                bin_num = CATEGORY_TO_BIN.get(category, 5) + 1
                bar = "█" * int(pct / 2.5)
                print(f"  Behälter {bin_num} ({category:8s}): {count:4d} ({pct:5.1f}%) {bar}")
        
        print("═" * 60 + "\n")
    
    def cleanup(self):
        """Aufräumen"""
        if self.enabled:
            self.belt_stop()
            if self.servo_pwm:
                self.servo_pwm.stop()
            GPIO.cleanup()
        
        self.print_stats()


# ══════════════════════════════════════════════════════════════
#                    KAMERA
# ══════════════════════════════════════════════════════════════

class Camera:
    """DroidCam USB-Kamera mit Thread-basiertem Capture"""
    
    def __init__(self):
        self.cap = None
        self.latest_frame = None
        self.frame_lock = Lock()
        self.running = False
        
    def connect(self) -> bool:
        """Verbindung zu DroidCam herstellen"""
        print("Verbinde zu DroidCam...")
        
        # ADB Port-Forwarding
        subprocess.run(
            ["adb", "forward", "tcp:4747", "tcp:4747"],
            capture_output=True
        )
        
        # Video-Stream öffnen
        self.cap = cv2.VideoCapture(f"{DROIDCAM_URL}/video")
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(f"{DROIDCAM_URL}/mjpegfeed")
        
        if not self.cap.isOpened():
            print("✗ Kamera nicht verfügbar!")
            print("  → DroidCam App starten und 'Start' drücken")
            return False
        
        # Buffer minimieren
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Capture-Thread starten
        self.running = True
        Thread(target=self._capture_loop, daemon=True).start()
        
        time.sleep(0.5)
        
        if self.latest_frame is not None:
            print("✓ Kamera verbunden!")
            return True
        else:
            print("✗ Keine Frames empfangen")
            return False
    
    def _capture_loop(self):
        """Hintergrund-Thread für Frame-Capture"""
        while self.running:
            try:
                for _ in range(2):
                    self.cap.grab()
                
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    with self.frame_lock:
                        self.latest_frame = frame
                        
            except Exception as e:
                print(f"Capture-Fehler: {e}")
                time.sleep(0.1)
            
            time.sleep(0.01)
    
    def get_frame(self):
        """Aktuelles Frame holen"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def get_jpeg(self, quality=90) -> bytes:
        """Frame als JPEG-Bytes für API"""
        frame = self.get_frame()
        if frame is not None:
            _, buffer = cv2.imencode(
                '.jpg', frame,
                [cv2.IMWRITE_JPEG_QUALITY, quality]
            )
            return buffer.tobytes()
        return None
    
    def trigger_autofocus(self):
        """Autofokus auslösen"""
        try:
            requests.get(f"{DROIDCAM_URL}/cam/1/af", timeout=1)
        except:
            pass
    
    def release(self):
        """Ressourcen freigeben"""
        self.running = False
        time.sleep(0.2)
        if self.cap:
            self.cap.release()


# ══════════════════════════════════════════════════════════════
#                    BRICKOGNIZE API
# ══════════════════════════════════════════════════════════════

class BrickognizeAPI:
    """Brickognize API Client"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def analyze(self, image_bytes: bytes) -> dict:
        """Bild analysieren"""
        try:
            files = {'query_image': ('lego.jpg', image_bytes, 'image/jpeg')}
            
            response = self.session.post(
                BRICKOGNIZE_URL,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    best = items[0]
                    return {
                        "success": True,
                        "id": best.get("id", "?"),
                        "name": best.get("name", "Unknown"),
                        "confidence": round(best.get("score", 0) * 100, 1)
                    }
                else:
                    return {"success": False, "error": "Nicht erkannt"}
            else:
                return {"success": False, "error": f"API-Fehler {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
#                    KATEGORISIERUNG
# ══════════════════════════════════════════════════════════════

def categorize_part(part_id: str, name: str) -> str:
    """Teil kategorisieren"""
    name_lower = name.lower()
    
    # Nach Schlüsselwörtern
    if "brick" in name_lower and "technic" not in name_lower:
        return "bricks"
    if "plate" in name_lower:
        return "plates"
    if "tile" in name_lower:
        return "tiles"
    if "slope" in name_lower or "wedge" in name_lower:
        return "slopes"
    if any(x in name_lower for x in ["technic", "axle", "beam", "pin", "gear"]):
        return "technic"
    
    # Nach Teil-ID Präfix
    prefixes = {
        "300": "bricks", "301": "bricks",
        "302": "plates", "303": "plates",
        "306": "tiles", "307": "tiles",
        "32": "technic", "40": "technic",
        "41": "slopes", "43": "slopes",
    }
    
    for prefix, category in prefixes.items():
        if part_id.startswith(prefix):
            return category
    
    return "unknown"


# ══════════════════════════════════════════════════════════════
#                    TERMINAL-AUSGABE
# ══════════════════════════════════════════════════════════════

def print_result(result: dict, category: str, bin_number: int):
    """Scan-Ergebnis im Terminal ausgeben"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print("\n" + "─" * 60)
    print(f"  [{timestamp}] TEIL ERKANNT")
    print("─" * 60)
    
    if result.get("success"):
        print(f"  Teil-ID:     {result['id']}")
        print(f"  Name:        {result['name']}")
        print(f"  Konfidenz:   {result['confidence']}%")
        print(f"  Kategorie:   {category}")
        print(f"  → Behälter:  {bin_number + 1}")
    else:
        print(f"  Fehler:      {result.get('error', 'Unbekannt')}")
        print(f"  → Behälter:  6 (Unbekannt)")
    
    print("─" * 60)


# ══════════════════════════════════════════════════════════════
#                    VORSCHAU-FENSTER
# ══════════════════════════════════════════════════════════════

class PreviewWindow:
    """Einfaches Vorschau-Fenster (nur Kamerabild)"""
    
    def __init__(self, window_name="LEGO Sortiermaschine"):
        self.window_name = window_name
        self.last_update = 0
        self.update_interval = 1.0 / PREVIEW_FPS
        
    def update(self, frame) -> int:
        """Vorschau aktualisieren, returns Tastendruck"""
        current_time = time.time()
        
        if current_time - self.last_update < self.update_interval:
            return cv2.waitKey(1) & 0xFF
        
        self.last_update = current_time
        
        if frame is not None:
            display = cv2.resize(frame, None, 
                                fx=PREVIEW_SCALE, 
                                fy=PREVIEW_SCALE)
            cv2.imshow(self.window_name, display)
        
        return cv2.waitKey(1) & 0xFF
    
    def close(self):
        cv2.destroyAllWindows()


# ══════════════════════════════════════════════════════════════
#                    SORTIERMASCHINE
# ══════════════════════════════════════════════════════════════

class LegoSorter:
    """Hauptklasse für die Sortiermaschine"""
    
    def __init__(self):
        self.camera = Camera()
        self.api = BrickognizeAPI()
        self.hardware = Hardware()
        self.preview = PreviewWindow()
        
    def initialize(self) -> bool:
        """System initialisieren"""
        print("\n" + "═" * 60)
        print("          LEGO SORTIERMASCHINE")
        print("═" * 60 + "\n")
        
        if not self.camera.connect():
            return False
        
        # Sensor-Test
        if self.hardware.enabled:
            status = self.hardware.get_sensor_status()
            print(f"\nSensor-Status: {status}")
        
        return True
    
    def scan_and_sort(self):
        """Ein Teil scannen und sortieren"""
        # Autofokus
        self.camera.trigger_autofocus()
        time.sleep(0.2)
        
        # Foto aufnehmen
        img_bytes = self.camera.get_jpeg()
        
        if not img_bytes:
            print("\n✗ Kamera-Fehler!")
            self.hardware.sort_to_category("unknown")
            return
        
        # Aktuelles Bild in Vorschau zeigen
        frame = self.camera.get_frame()
        if frame is not None:
            display = cv2.resize(frame, None, fx=PREVIEW_SCALE, fy=PREVIEW_SCALE)
            cv2.imshow(self.preview.window_name, display)
            cv2.waitKey(1)
        
        # API-Aufruf
        print("\n  Analysiere...", end="", flush=True)
        result = self.api.analyze(img_bytes)
        
        if result.get("success"):
            category = categorize_part(result["id"], result["name"])
            bin_number = CATEGORY_TO_BIN.get(category, 5)
            
            # Terminal-Ausgabe
            print_result(result, category, bin_number)
            
            # Sortieren
            self.hardware.sort_to_category(category)
        else:
            print_result(result, "unknown", 5)
            self.hardware.sort_to_category("unknown")
    
    def run_automatic(self):
        """Automatischer Sortiermodus"""
        print("\n" + "═" * 60)
        print("          AUTOMATISCHER MODUS")
        print("═" * 60)
        print("\n  Warte auf Teile...")
        print("  [Q] im Fenster oder Strg+C zum Beenden")
        print("\n" + "─" * 60)
        
        self.hardware.belt_start()
        last_detection = False
        
        try:
            while True:
                # Vorschau aktualisieren
                frame = self.camera.get_frame()
                key = self.preview.update(frame)
                
                if key == ord('q'):
                    print("\n\nBeende...")
                    break
                
                # Sensor prüfen
                part_detected = self.hardware.is_part_detected()
                
                # Status-Zeile
                status = ">>> TEIL <<<" if part_detected else "    frei    "
                parts = self.hardware.total_parts
                print(f"\r  Sensor: [{status}] | Teile: {parts} ", end="", flush=True)
                
                # Flanken-Erkennung (Teil neu erkannt)
                if part_detected and not last_detection:
                    print("\n\n>>> TEIL ERKANNT <<<")
                    
                    # Band stoppen
                    self.hardware.belt_stop()
                    time.sleep(SCAN_DELAY)
                    
                    # Scannen und sortieren
                    self.scan_and_sort()
                    
                    # Band starten
                    time.sleep(BELT_RESTART_DELAY)
                    self.hardware.belt_start()
                    print("\n  Warte auf nächstes Teil...")
                
                last_detection = part_detected
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n⚠ Abbruch durch Benutzer")
        
        finally:
            self.hardware.belt_stop()
    
    def run_interactive(self):
        """Interaktiver Modus"""
        print("\n" + "═" * 60)
        print("          INTERAKTIVER MODUS")
        print("═" * 60)
        print("\n  Tasten (im Fenster):")
        print("    [LEERTASTE] = Scannen")
        print("    [B]         = Band an/aus")
        print("    [S]         = Statistik")
        print("    [Q]         = Beenden")
        print("\n" + "─" * 60)
        
        try:
            while True:
                frame = self.camera.get_frame()
                key = self.preview.update(frame)
                
                if key == ord('q'):
                    print("\nBeende...")
                    break
                
                elif key == ord(' '):
                    print("\n>>> MANUELLER SCAN <<<")
                    if self.hardware.belt_running:
                        self.hardware.belt_stop()
                    time.sleep(SCAN_DELAY)
                    self.scan_and_sort()
                
                elif key == ord('b'):
                    if self.hardware.belt_running:
                        self.hardware.belt_stop()
                    else:
                        self.hardware.belt_start()
                
                elif key == ord('s'):
                    self.hardware.print_stats()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n⚠ Abbruch durch Benutzer")
        
        finally:
            self.hardware.belt_stop()
    
    def run_sensor_test(self):
        """Sensor-Testmodus"""
        print("\n" + "═" * 60)
        print("          SENSOR-TEST")
        print("═" * 60)
        print("\n  Bewege ein Teil durch die Lichtschranke.")
        print("  [Q] zum Beenden")
        print("\n" + "─" * 60)
        
        try:
            while True:
                frame = self.camera.get_frame()
                key = self.preview.update(frame)
                
                if key == ord('q'):
                    break
                
                detected = self.hardware.is_part_detected()
                status = "█████ TEIL █████" if detected else "      frei      "
                print(f"\r  Sensor: [{status}]", end="", flush=True)
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            pass
        
        print("\n")
    
    def shutdown(self):
        """System herunterfahren"""
        print("\nFahre herunter...")
        self.camera.release()
        self.preview.close()
        self.hardware.cleanup()


# ══════════════════════════════════════════════════════════════
#                    SIMULATION
# ══════════════════════════════════════════════════════════════

def run_simulation(sorter: LegoSorter):
    """Simulation ohne Hardware"""
    print("\n" + "═" * 60)
    print("          SIMULATIONS-MODUS")
    print("═" * 60)
    print("\n  Keine Hardware erkannt.")
    print("  [T] oder [LEERTASTE] = Teil simulieren")
    print("  [Q] = Beenden")
    print("\n" + "─" * 60)
    
    try:
        while True:
            frame = sorter.camera.get_frame()
            key = sorter.preview.update(frame)
            
            if key == ord('q'):
                break
            
            elif key == ord('t') or key == ord(' '):
                print("\n>>> SIMULIERTER TRIGGER <<<")
                sorter.scan_and_sort()
            
            elif key == ord('s'):
                sorter.hardware.print_stats()
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        pass


# ══════════════════════════════════════════════════════════════
#                    HAUPTPROGRAMM
# ══════════════════════════════════════════════════════════════

def main():
    sorter = LegoSorter()
    
    if not sorter.initialize():
        print("\n✗ Initialisierung fehlgeschlagen!")
        return
    
    # Modus wählen
    print("\n  Modus wählen:")
    print("    1. Automatisch (mit Lichtschranke)")
    print("    2. Interaktiv (manueller Trigger)")
    print("    3. Sensor-Test")
    
    if not HAS_GPIO:
        print("    4. Simulation")
    
    print()
    
    try:
        choice = input("  Auswahl [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"
    
    try:
        if choice == "2":
            sorter.run_interactive()
        elif choice == "3":
            sorter.run_sensor_test()
        elif choice == "4" or not HAS_GPIO:
            run_simulation(sorter)
        else:
            sorter.run_automatic()
            
    finally:
        sorter.shutdown()


if __name__ == "__main__":
    main()