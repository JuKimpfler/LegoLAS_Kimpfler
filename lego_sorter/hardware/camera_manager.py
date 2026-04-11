"""
Kamera-Manager für LegoLAS.
Verwendet DroidCam via HTTP-Stream (WLAN-Modus, lokales Netzwerk).

Liefert Frames als numpy-Array (BGR) bzw. als PIL-Image für tkinter.
"""

import logging
import threading
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("OpenCV nicht verfügbar – Kamera-Mock wird verwendet.")

try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("Pillow nicht verfügbar.")


class CameraManager:
    """
    Thread-sichere Kamera-Verwaltung mit kontinuierlichem Capture-Loop.
    Verwendet ausschließlich DroidCam via HTTP-Stream (WLAN, lokales Netzwerk).

    Parameter
    ---------
    config : module
        Konfigurationsmodul mit DROIDCAM_URL, CAMERA_WIDTH, CAMERA_HEIGHT, LIVE_FPS.
    """

    def __init__(self, config):
        self.cfg = config
        self._cap = None
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_counter: int = 0   # Wird bei jedem neuen Frame erhöht
        self._last_frame_ts: float = 0.0   # Zeitstempel des letzten empfangenen Frames
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lebenszyklus
    # ------------------------------------------------------------------

    def start(self):
        """Öffnet DroidCam-Stream und startet Capture-Loop in eigenem Thread."""
        if self._running:
            return
        if not _CV2_AVAILABLE:
            logger.warning("cv2 fehlt – Kamera-Dummy aktiv.")
            self._running = True
            self._thread = threading.Thread(target=self._dummy_loop,
                                            daemon=True)
            self._thread.start()
            return

        self._cap = cv2.VideoCapture(self.cfg.DROIDCAM_URL)

        if self._cap is None or not self._cap.isOpened():
            logger.error(
                "DroidCam-Stream konnte nicht geöffnet werden (%s). "
                "Bitte sicherstellen, dass: "
                "1) DroidCam-App auf dem Handy läuft, "
                "2) Handy und Raspberry Pi im selben WLAN sind, "
                "3) die korrekte IP-Adresse in config.py eingetragen ist.",
                self.cfg.DROIDCAM_URL,
            )
            self._cap = None
            self._running = True
            self._thread = threading.Thread(target=self._dummy_loop,
                                            daemon=True)
            self._thread.start()
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.CAMERA_HEIGHT)
        # Puffergröße minimieren, um Lag im HTTP-Stream zu reduzieren
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("DroidCam-Stream gestartet (%s).", self.cfg.DROIDCAM_URL)

    def stop(self):
        """Stoppt den Capture-Loop und gibt Ressourcen frei."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("Kamera gestoppt.")

    # ------------------------------------------------------------------
    # Interne Loops
    # ------------------------------------------------------------------

    def _capture_loop(self):
        # Frames so schnell wie möglich lesen, um den internen
        # OpenCV/FFMPEG-Puffer leer zu halten und stets den neuesten Frame
        # zu erhalten. Dadurch wird der typische 10-Sekunden-Lag bei
        # DroidCam-over-HTTP (MJPEG) eliminiert.
        # Nach jedem erfolgreichen Lesevorgang kurz schlafen, damit der GIL
        # für andere Threads (insbesondere den tkinter-Main-Thread) freigegeben
        # wird. DroidCam liefert maximal ~30 fps; 5 ms Pause haben keinen
        # Einfluss auf die Frame-Frische, reduzieren aber den CPU-Verbrauch
        # erheblich.
        while self._running:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._latest_frame = frame
                    self._frame_counter += 1
                    self._last_frame_ts = time.time()
                time.sleep(0.005)
            else:
                # Kurze Pause bei Lesefehler, um CPU zu schonen
                time.sleep(0.05)

    def _dummy_loop(self):
        """Erzeugt graue Platzhalter-Frames wenn kein DroidCam-Stream verfügbar."""
        interval = 1.0 / max(1, self.cfg.LIVE_FPS)
        while self._running:
            frame = np.full(
                (self.cfg.CAMERA_HEIGHT, self.cfg.CAMERA_WIDTH, 3),
                fill_value=50,
                dtype=np.uint8,
            )
            if _CV2_AVAILABLE:
                cv2.putText(frame, "DroidCam nicht verbunden", (40, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (180, 180, 180), 2)
                cv2.putText(frame, "IP-Adresse in config.py prüfen", (40, 260),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 140, 140), 1)
            with self._lock:
                self._latest_frame = frame
                self._frame_counter += 1
            time.sleep(interval)

    # ------------------------------------------------------------------
    # Öffentliche API
    # ------------------------------------------------------------------

    @property
    def frame_counter(self) -> int:
        """Zähler der bisher empfangenen Frames – nützlich für Change-Detection."""
        with self._lock:
            return self._frame_counter

    @property
    def last_frame_ts(self) -> float:
        """Unix-Zeitstempel (time.time()) des zuletzt empfangenen Frames."""
        with self._lock:
            return self._last_frame_ts

    @property
    def seconds_since_last_frame(self) -> float:
        """Sekunden seit dem letzten empfangenen Frame.

        Gibt ``math.inf`` zurück, wenn noch kein Frame empfangen wurde
        (d. h. ``last_frame_ts`` ist 0.0).
        """
        with self._lock:
            if self._last_frame_ts == 0.0:
                return float("inf")
            return time.time() - self._last_frame_ts

    def get_frame(self) -> Optional[np.ndarray]:
        """Gibt den aktuellsten Frame als BGR-Array zurück."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def capture_image(self) -> Optional[np.ndarray]:
        """
        Macht ein Einzelfoto (identisch mit get_frame aber semantisch
        klar als »Scan-Aufnahme«).
        """
        return self.get_frame()

    def get_pil_image(self, width: int = None,
                      height: int = None) -> Optional["Image.Image"]:
        """Gibt den aktuellen Frame als PIL-Image zurück (für tkinter)."""
        if not _PIL_AVAILABLE:
            return None
        frame = self.get_frame()
        if frame is None:
            return None
        if _CV2_AVAILABLE:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            rgb = frame
        img = Image.fromarray(rgb)
        if width and height:
            # BILINEAR ist deutlich schneller als LANCZOS und für Live-Vorschau ausreichend
            img = img.resize((width, height), Image.BILINEAR)
        return img

    def frame_to_jpeg_bytes(self, frame: np.ndarray,
                             quality: int = 90) -> Optional[bytes]:
        """
        Kodiert einen Frame als JPEG-Bytes (für den Brickognize-Upload).
        """
        if not _CV2_AVAILABLE:
            return None
        ok, buf = cv2.imencode(".jpg", frame,
                               [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok:
            return bytes(buf)
        return None

    @property
    def is_open(self) -> bool:
        return self._running

