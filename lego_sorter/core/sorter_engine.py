"""
Sortier-Engine für LegoLAS.

Implementiert die Zustandsmaschine für den automatischen Sortierbetrieb:

  IDLE → WAITING_FOR_PART → STOPPING_BELT → SCANNING →
  SORTING (Servo stellen) → BELT_RESTART → IDLE

Unterstützt zwei Modi:
  - SORT_MODE   : Teile werden nach Typ sortiert (Inventar aufbauen).
  - ORDER_MODE  : Teile werden gemäß aktivem Auftrag sortiert.
"""

import logging
import threading
import time
from enum import Enum, auto
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SortMode(Enum):
    SORT  = auto()   # freies Sortieren
    ORDER = auto()   # Auftragsabarbeitung


class SorterState(Enum):
    IDLE               = auto()
    WAITING_FOR_PART   = auto()
    STOPPING_BELT      = auto()
    SCANNING           = auto()
    SORTING            = auto()
    BELT_RESTART       = auto()
    ERROR              = auto()
    PAUSED             = auto()


class SorterEngine:
    """
    Kontrolliert den automatischen Sortierprozess.

    Callbacks (alle optional, im GUI-Thread via ``after()`` aufrufen):
      on_state_change(state: SorterState)
      on_part_identified(part_num, name, score, container)
      on_part_unknown(container=6)
      on_error(message)
    """

    FALLBACK_CONTAINER = 6   # Unbekannte Teile

    def __init__(self, gpio_ctrl, camera_mgr, brickognize_client, database,
                 config):
        self.gpio   = gpio_ctrl
        self.cam    = camera_mgr
        self.api    = brickognize_client
        self.db     = database
        self.cfg    = config

        self._mode            = SortMode.SORT
        self._active_order_id: Optional[int] = None
        self._state           = SorterState.IDLE
        self._running         = False
        self._thread: Optional[threading.Thread] = None
        self._lock            = threading.Lock()

        # Servo-Positionen aus DB laden
        self._servo_positions: dict = {}
        self._reload_servo_positions()

        # Einstellungen
        self._belt_speed     = config.DEFAULT_BELT_SPEED
        self._conf_threshold = config.DEFAULT_CONF_THRESHOLD

        # Callbacks
        self.on_state_change:       Optional[Callable] = None
        self.on_part_identified:    Optional[Callable] = None
        self.on_part_unknown:       Optional[Callable] = None
        self.on_error:              Optional[Callable] = None

    # ------------------------------------------------------------------
    # Öffentliche Steuerung
    # ------------------------------------------------------------------

    def start(self, mode: SortMode = None, order_id: int = None):
        """Startet den automatischen Sortier-Loop."""
        if self._running:
            return
        if mode:
            self._mode = mode
        if order_id is not None:
            self._active_order_id = order_id
        self._reload_servo_positions()
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("SorterEngine gestartet (mode=%s).", self._mode)

    def stop(self):
        """Stoppt den automatischen Loop."""
        self._running = False
        self.gpio.belt_stop()
        self._set_state(SorterState.IDLE)
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info("SorterEngine gestoppt.")

    def pause(self):
        self._set_state(SorterState.PAUSED)
        self.gpio.belt_stop()

    def resume(self):
        if self._state == SorterState.PAUSED:
            self._set_state(SorterState.WAITING_FOR_PART)
            self.gpio.belt_start(self._belt_speed)

    def manual_scan(self) -> Optional[dict]:
        """
        Führt einen manuellen Scan durch und gibt das Ergebnis zurück.
        Das Band läuft während des Scans nicht.
        """
        frame = self.cam.capture_image()
        if frame is None:
            logger.error("Kein Frame für manuellen Scan.")
            return None
        return self._do_scan(frame)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> SorterState:
        return self._state

    @property
    def mode(self) -> SortMode:
        return self._mode

    @mode.setter
    def mode(self, value: SortMode):
        self._mode = value

    @property
    def belt_speed(self) -> int:
        return self._belt_speed

    @belt_speed.setter
    def belt_speed(self, value: int):
        self._belt_speed = max(0, min(100, value))
        self.gpio.belt_speed = self._belt_speed

    @property
    def conf_threshold(self) -> float:
        return self._conf_threshold

    @conf_threshold.setter
    def conf_threshold(self, value: float):
        self._conf_threshold = max(0.0, min(1.0, value))

    # ------------------------------------------------------------------
    # Interne Schleife
    # ------------------------------------------------------------------

    def _run_loop(self):
        self._set_state(SorterState.WAITING_FOR_PART)
        self.gpio.belt_start(self._belt_speed)

        while self._running:
            if self._state == SorterState.PAUSED:
                time.sleep(0.1)
                continue

            # 1. Auf Teil warten
            if not self.gpio.sensor_read():
                time.sleep(0.01)
                continue

            # 2. Teil erkannt → Band stoppen
            self._set_state(SorterState.STOPPING_BELT)
            self.gpio.belt_stop()
            time.sleep(self.cfg.BELT_STOP_DELAY)

            # 3. Scannen
            self._set_state(SorterState.SCANNING)
            frame = self.cam.capture_image()
            if frame is None:
                logger.error("Kein Frame erhalten.")
                container = self.FALLBACK_CONTAINER
                result = None
            else:
                result = self._do_scan(frame)
                if result:
                    container = result["container"]
                else:
                    container = self.FALLBACK_CONTAINER

            # 4. Sortieren
            self._set_state(SorterState.SORTING)
            self._reload_servo_positions()
            self.gpio.servo_to_position(container, self._servo_positions)

            # 5. Band kurz weiter lassen bis Teil gefallen
            self._set_state(SorterState.BELT_RESTART)
            self.gpio.belt_start(self._belt_speed)
            time.sleep(1.5)
            # Warte bis Sensor wieder frei
            self.gpio.wait_for_clear(timeout=3.0)

            # 6. Zurück zur Warteposition
            self._set_state(SorterState.WAITING_FOR_PART)

        self._set_state(SorterState.IDLE)

    # ------------------------------------------------------------------
    # Hilfsmethoden
    # ------------------------------------------------------------------

    def _do_scan(self, frame) -> Optional[dict]:
        """Scannt einen Frame und gibt Ergebnis-Dict zurück."""
        image_bytes = self.cam.frame_to_jpeg_bytes(frame)
        if image_bytes is None:
            return None

        result = self.api.best_match(image_bytes,
                                     threshold=self._conf_threshold)
        if result:
            container = self._determine_container(result.part_num)
            data = {
                "part_num":  result.part_num,
                "name":      result.name,
                "score":     result.score,
                "container": container,
            }
            # In DB speichern
            self.db.add_part(result.part_num, result.name, container)
            self.db.log_scan(result.part_num, result.name, result.score,
                             container, self._active_order_id)
            if self._mode == SortMode.ORDER and self._active_order_id:
                self.db.fulfill_order_item(
                    self._active_order_id, result.part_num, container)

            if self.on_part_identified:
                self.on_part_identified(
                    result.part_num, result.name, result.score, container)
            logger.info("Teil erkannt: %s → Behälter %d (score=%.2f)",
                        result.part_num, container, result.score)
            return data
        else:
            self.db.add_part("???", "Unbekannt", self.FALLBACK_CONTAINER)
            self.db.log_scan("???", "Unbekannt", 0.0, self.FALLBACK_CONTAINER,
                             self._active_order_id)
            if self.on_part_unknown:
                self.on_part_unknown(self.FALLBACK_CONTAINER)
            logger.info("Teil nicht erkannt → Behälter %d",
                        self.FALLBACK_CONTAINER)
            return None

    def _determine_container(self, part_num: str) -> int:
        """
        Bestimmt den Zielbehälter für ein Teil.

        Im ORDER_MODE: prüft aktiven Auftrag nach Priorität.
        Im SORT_MODE:  prüft Inventar, sonst Behälter 1.
        """
        if self._mode == SortMode.ORDER and self._active_order_id:
            items = self.db.get_order_items(self._active_order_id)
            for item in sorted(items, key=lambda x: x["container"]):
                if (item["part_num"] == part_num and
                        item["fulfilled"] < item["required"]):
                    return item["container"]
        # SORT_MODE oder Teil nicht im Auftrag: Standardbehälter prüfen
        inventory = self.db.get_inventory()
        for entry in inventory:
            if entry["part_num"] == part_num:
                return entry["container"]
        return 1  # Neues Teil → Behälter 1

    def _set_state(self, state: SorterState):
        with self._lock:
            self._state = state
        if self.on_state_change:
            self.on_state_change(state)
        logger.debug("Zustand: %s", state.name)

    def _reload_servo_positions(self):
        self._servo_positions = self.db.get_servo_positions()
