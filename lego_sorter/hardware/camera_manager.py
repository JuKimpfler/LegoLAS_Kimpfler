"""
Kamera-Manager für LegoLAS.
Unterstützt:
  1. Direkte OpenCV-Kamera (/dev/video0 o.ä.)
  2. DroidCam via HTTP-Stream (USB-Modus)

Liefert Frames als numpy-Array (BGR) bzw. als PIL-Image für tkinter.
"""

import io
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

    Parameter
    ---------
    config : module
        Konfigurationsmodul mit CAMERA_INDEX, DROIDCAM_URL, etc.
    use_droidcam : bool
        Falls True wird der HTTP-Stream von DroidCam verwendet.
    """

    def __init__(self, config, use_droidcam: bool = False):
        self.cfg = config
        self._use_droidcam = use_droidcam
        self._cap = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lebenszyklus
    # ------------------------------------------------------------------

    def start(self):
        """Öffnet Kamera und startet Capture-Loop in eigenem Thread."""
        if self._running:
            return
        if not _CV2_AVAILABLE:
            logger.warning("cv2 fehlt – Kamera-Dummy aktiv.")
            self._running = True
            self._thread = threading.Thread(target=self._dummy_loop,
                                            daemon=True)
            self._thread.start()
            return

        if self._use_droidcam:
            self._cap = cv2.VideoCapture(self.cfg.DROIDCAM_URL)
        else:
            self._cap = cv2.VideoCapture(self.cfg.CAMERA_INDEX)

        if self._cap is None or not self._cap.isOpened():
            logger.error("Kamera konnte nicht geöffnet werden.")
            self._cap = None
            self._running = True
            self._thread = threading.Thread(target=self._dummy_loop,
                                            daemon=True)
            self._thread.start()
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.CAMERA_HEIGHT)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Kamera gestartet (droidcam=%s).", self._use_droidcam)

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
        interval = 1.0 / max(1, self.cfg.LIVE_FPS)
        while self._running:
            t0 = time.time()
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._latest_frame = frame
            elapsed = time.time() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _dummy_loop(self):
        """Erzeugt graue Platzhalter-Frames wenn keine Kamera vorhanden."""
        interval = 1.0 / max(1, self.cfg.LIVE_FPS)
        while self._running:
            frame = np.full(
                (self.cfg.CAMERA_HEIGHT, self.cfg.CAMERA_WIDTH, 3),
                fill_value=50,
                dtype=np.uint8,
            )
            # Beschriftung
            if _CV2_AVAILABLE:
                cv2.putText(frame, "Keine Kamera", (80, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (180, 180, 180), 2)
            with self._lock:
                self._latest_frame = frame
            time.sleep(interval)

    # ------------------------------------------------------------------
    # Öffentliche API
    # ------------------------------------------------------------------

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
            img = img.resize((width, height), Image.LANCZOS)
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
