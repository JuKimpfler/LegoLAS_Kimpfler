"""
Sortier-Ansicht für LegoLAS GUI.

Enthält:
  - Kamera-Statusanzeige (kein Live-Bild – nur FPS und Verbindungsstatus)
  - Status-Panel (Zustand, letztes Teil, Behälter)
  - Manuelle Steuerung (Band, Scan, Weiche)
  - Umschaltung Manuell / Automatik
  - Umschaltung Sortiermodus / Auftragsmodus

Tastaturkürzel:
  B        – Band an/aus
  Space    – Manuell scannen
  A        – Auto-Modus an/aus
  1–6      – Weiche manuell stellen

Performance-Hinweise (Raspberry Pi 3B):
  - Kein Live-Kamerabild in der GUI – spart erheblich CPU/RAM auf dem Pi 3.
  - Stattdessen wird eine leichte Statuskarte angezeigt (online/offline, FPS).
  - Kamera-Loop und Sensor-Loop sind entkoppelt.
  - Beide Loops werden bei on_hide() pausiert und bei on_show() fortgesetzt.
  - Label-Updates erfolgen nur bei tatsächlichen Wertänderungen.
  - Manueller Scan läuft in einem eigenen Thread, damit der Tkinter-Main-Thread
    nicht durch den blockierenden Brickognize-API-Aufruf einfriert.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
import sys, os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from core.sorter_engine import SorterState, SortMode
from .base import BaseView


class SortView(BaseView):

    def _build_ui(self):
        self._sensor_state       = None   # Letzter bekannter Sensor-Zustand
        self._camera_after_id    = None   # ID des laufenden after()-Callbacks
        self._sensor_after_id    = None

        # FPS-Berechnung
        self._fps_counter_prev   = 0
        self._fps_time_prev      = time.monotonic()
        self._current_fps        = 0.0

        # Zweispaltiges Layout: linke + rechte Spalte gleichgewichtig
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Linke Spalte: Kamera-Status + Moduswahl ───────────────────────
        left_frame = ttk.Frame(self, style="TFrame")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left_frame.columnconfigure(0, weight=1)

        self._build_camera_status(left_frame)
        self._build_mode_switcher(left_frame)

        # ── Rechte Spalte: Systemstatus + Steuerung ───────────────────────
        right_frame = ttk.Frame(self, style="TFrame")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right_frame.columnconfigure(0, weight=1)

        self._build_status(right_frame)
        self._build_manual_controls(right_frame)
        self._build_container_buttons(right_frame)

    # ------------------------------------------------------------------
    # Kamera-Statuskarte (leichtgewichtig – kein Live-Bild)
    # ------------------------------------------------------------------

    def _build_camera_status(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        frm.columnconfigure(1, weight=1)

        # Kopfzeile: Titel + Sensor-Indikator
        header = ttk.Frame(frm, style="Surface.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=10, pady=(8, 4))
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="📷  Kamera",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, sticky="w")

        self._lbl_sensor = tk.Label(
            header,
            text="○  frei",
            bg=cfg.THEME_SURFACE,
            fg=cfg.THEME_ACCENT2,
            font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
            anchor="e",
        )
        self._lbl_sensor.grid(row=0, column=1, sticky="e", padx=(8, 0))

        ttk.Separator(frm, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        # Verbindungsstatus
        ttk.Label(frm, text="Status:",
                  style="Surface.Muted.TLabel").grid(
            row=2, column=0, padx=10, pady=5, sticky="w")
        self._lbl_cam_status = ttk.Label(frm, text="–",
                                          style="Surface.TLabel",
                                          foreground=cfg.THEME_MUTED)
        self._lbl_cam_status.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # FPS-Anzeige
        ttk.Label(frm, text="FPS:",
                  style="Surface.Muted.TLabel").grid(
            row=3, column=0, padx=10, pady=(0, 10), sticky="w")
        self._lbl_cam_fps = ttk.Label(frm, text="–",
                                       style="Surface.TLabel",
                                       foreground=cfg.THEME_MUTED)
        self._lbl_cam_fps.grid(row=3, column=1, padx=10, pady=(0, 10),
                                sticky="w")

    # ------------------------------------------------------------------
    # Status-Panel
    # ------------------------------------------------------------------

    def _build_status(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        frm.columnconfigure(1, weight=1)

        # Titelzeile
        ttk.Label(frm, text="Status",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, columnspan=2,
            padx=10, pady=(8, 4), sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        rows = [
            ("Zustand:",      "_lbl_state",     cfg.THEME_ACCENT),
            ("Letztes Teil:", "_lbl_part",      cfg.THEME_TEXT),
            ("Behälter:",     "_lbl_container", cfg.THEME_ACCENT2),
        ]
        for idx, (caption, attr, color) in enumerate(rows, start=2):
            ttk.Label(frm, text=caption,
                      style="Surface.Muted.TLabel").grid(
                row=idx, column=0, padx=10, pady=5, sticky="w")
            lbl = ttk.Label(frm, text="–",
                            style="Surface.TLabel",
                            foreground=color,
                            wraplength=210)
            lbl.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            setattr(self, attr, lbl)

    # ------------------------------------------------------------------
    # Moduswahl
    # ------------------------------------------------------------------

    def _build_mode_switcher(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        frm.columnconfigure((0, 1), weight=1)

        ttk.Label(frm, text="Betrieb",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        self._auto_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(frm, text="Manuell  [F2]",
                        variable=self._auto_var, value=False,
                        command=self._on_mode_change,
                        style="Surface.TRadiobutton").grid(
            row=2, column=0, padx=10, pady=4, sticky="w")
        ttk.Radiobutton(frm, text="Automatik  [A]",
                        variable=self._auto_var, value=True,
                        command=self._on_mode_change,
                        style="Surface.TRadiobutton").grid(
            row=2, column=1, padx=10, pady=4, sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=4)

        ttk.Label(frm, text="Modus",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=4, column=0, columnspan=2, padx=10, pady=(4, 2), sticky="w")

        self._sort_mode_var = tk.StringVar(value="sort")
        ttk.Radiobutton(frm, text="Sortiermodus",
                        variable=self._sort_mode_var, value="sort",
                        command=self._on_sort_mode_change,
                        style="Surface.TRadiobutton").grid(
            row=5, column=0, padx=10, pady=4, sticky="w")
        ttk.Radiobutton(frm, text="Auftragsmodus",
                        variable=self._sort_mode_var, value="order",
                        command=self._on_sort_mode_change,
                        style="Surface.TRadiobutton").grid(
            row=5, column=1, padx=10, pady=4, sticky="w")

        ttk.Label(frm, text="Aktiver Auftrag:",
                  style="Surface.Muted.TLabel").grid(
            row=6, column=0, padx=10, pady=(4, 2), sticky="w")
        self._order_var = tk.StringVar(value="")
        self._order_combo = ttk.Combobox(frm, textvariable=self._order_var,
                                          state="readonly", width=17)
        self._order_combo.grid(row=6, column=1, padx=10, pady=(4, 8),
                                sticky="ew")
        self._order_combo.bind("<<ComboboxSelected>>", self._on_order_selected)
        self._refresh_order_list()

    # ------------------------------------------------------------------
    # Manuelle Steuerung
    # ------------------------------------------------------------------

    def _build_manual_controls(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        frm.columnconfigure((0, 1), weight=1)

        ttk.Label(frm, text="Manuelle Steuerung",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        self._btn_belt = ttk.Button(frm, text="▶  Band starten  [B]",
                                     command=self._toggle_belt,
                                     style="Accent.TButton")
        self._btn_belt.grid(row=2, column=0, padx=8, pady=4, sticky="ew")

        self._btn_scan = ttk.Button(frm, text="📷  Scannen  [Space]",
                                    command=self._manual_scan,
                                    style="TButton")
        self._btn_scan.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

    # ------------------------------------------------------------------
    # Behälter-Schnellauswahl
    # ------------------------------------------------------------------

    def _build_container_buttons(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        for i in range(6):
            frm.columnconfigure(i, weight=1)

        ttk.Label(frm, text="Weiche stellen  [1–6]",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, columnspan=6, padx=10, pady=(8, 4), sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=(0, 6))

        for i in range(1, 7):
            ttk.Button(frm, text=str(i),
                       command=lambda n=i: self._set_container(n),
                       style="TButton").grid(
                row=2, column=i - 1, padx=3, pady=(0, 8), sticky="ew")

    # ------------------------------------------------------------------
    # Kamera-Status-Update (leichtgewichtig – kein Live-Bild)
    # ------------------------------------------------------------------

    def _update_camera(self):
        if not self.winfo_exists():
            return
        cam = self.app.camera

        now = time.monotonic()
        elapsed = now - self._fps_time_prev
        if elapsed >= 1.0:
            if cam:
                counter = cam.frame_counter
                self._current_fps = (counter - self._fps_counter_prev) / elapsed
                self._fps_counter_prev = counter
                self._fps_time_prev = now
            else:
                self._fps_time_prev = now

        if cam and cam.is_open:
            lag = cam.seconds_since_last_frame
            if math.isinf(lag):
                status_text  = "verbunden – warte auf Frame…"
                status_color = cfg.THEME_WARNING
            elif lag > 5:
                status_text  = f"⚠️  hängt ({lag:.0f} s kein Frame)"
                status_color = cfg.THEME_DANGER
            else:
                status_text  = "✅  verbunden"
                status_color = cfg.THEME_ACCENT2
        else:
            status_text  = "❌  offline"
            status_color = cfg.THEME_DANGER
            self._current_fps = 0.0

        self._lbl_cam_status.configure(text=status_text,
                                        foreground=status_color)
        fps_text = f"{self._current_fps:.1f}" if cam and cam.is_open else "–"
        self._lbl_cam_fps.configure(text=fps_text)

        interval_ms = int(1000 / max(1, cfg.GUI_STATUS_FPS))
        self._camera_after_id = self.after(interval_ms, self._update_camera)

    # ------------------------------------------------------------------
    # Sensor-Poll (leichtgewichtig, unabhängig von der Kamera)
    # ------------------------------------------------------------------

    def _poll_sensor(self):
        if not self.winfo_exists():
            return
        gpio = self.app.gpio
        if gpio:
            detected = gpio.sensor_read()
            if detected != self._sensor_state:
                self._sensor_state = detected
                if detected:
                    self._lbl_sensor.configure(
                        text="◉  TEIL ERKANNT",
                        fg=cfg.THEME_DANGER)
                else:
                    self._lbl_sensor.configure(
                        text="○  frei",
                        fg=cfg.THEME_ACCENT2)

        self._sensor_after_id = self.after(cfg.SENSOR_POLL_MS,
                                            self._poll_sensor)

    # ------------------------------------------------------------------
    # Sichtbarkeits-Hooks (Loops starten/stoppen)
    # ------------------------------------------------------------------

    def on_show(self):
        self._refresh_order_list()
        if self._camera_after_id is None:
            self._update_camera()
        if self._sensor_after_id is None:
            self._poll_sensor()

    def on_hide(self):
        if self._camera_after_id is not None:
            self.after_cancel(self._camera_after_id)
            self._camera_after_id = None
        if self._sensor_after_id is not None:
            self.after_cancel(self._sensor_after_id)
            self._sensor_after_id = None

    # ------------------------------------------------------------------
    # Event-Handler
    # ------------------------------------------------------------------

    def _toggle_belt(self):
        gpio = self.app.gpio
        if not gpio:
            return
        if gpio.belt_running:
            gpio.belt_stop()
            self._btn_belt.configure(text="▶  Band starten  [B]",
                                     style="Accent.TButton")
        else:
            gpio.belt_start()
            self._btn_belt.configure(text="⏹  Band stoppen  [B]",
                                     style="Danger.TButton")

    def _manual_scan(self):
        engine = self.app.engine
        if not engine:
            return
        # Scan-Button sperren, damit kein Doppelklick möglich ist
        self._btn_scan.configure(state="disabled", text="⏳  Scanne…")

        def _do_scan():
            result = engine.manual_scan()
            # Ergebnis im Tkinter-Main-Thread verarbeiten
            self.after(0, lambda: self._on_manual_scan_done(result))

        threading.Thread(target=_do_scan, daemon=True).start()

    def _on_manual_scan_done(self, result):
        """Wird im Main-Thread aufgerufen, nachdem der manuelle Scan abgeschlossen ist."""
        self._btn_scan.configure(state="normal", text="📷  Scannen  [Space]")
        if result:
            color = result.get("color_name", "")
            part_text = (
                f"{result['part_num']} – {result['name']} ({color})  "
                f"[{result['score']:.0%}]"
                if color else
                f"{result['part_num']} – {result['name']}  "
                f"[{result['score']:.0%}]"
            )
            self._lbl_part.configure(text=part_text)
            self._lbl_container.configure(
                text=f"Behälter {result['container']}")
        else:
            self._lbl_part.configure(text="Nicht erkannt")
            self._lbl_container.configure(
                text=f"Behälter {self.app.engine.FALLBACK_CONTAINER}")

    def _set_container(self, n: int):
        gpio = self.app.gpio
        db = self.app.db
        if not gpio or not db:
            return
        positions = db.get_servo_positions()
        gpio.servo_to_position(n, positions)
        self._lbl_container.configure(text=f"Weiche → {n}")

    def _on_mode_change(self):
        engine = self.app.engine
        if not engine:
            return
        if self._auto_var.get():
            mode = (SortMode.ORDER
                    if self._sort_mode_var.get() == "order"
                    else SortMode.SORT)
            order_id = self.app.active_order_id
            engine.start(mode=mode, order_id=order_id)
        else:
            engine.stop()

    def _on_sort_mode_change(self):
        if self._auto_var.get():
            self._on_mode_change()

    def _on_order_selected(self, _event=None):
        sel = self._order_var.get()
        for order in self._orders_cache:
            if order["name"] == sel:
                self.app.active_order_id = order["id"]
                break

    def _refresh_order_list(self):
        db = self.app.db
        if not db:
            return
        self._orders_cache = db.get_orders()
        names = [o["name"] for o in self._orders_cache]
        self._order_combo["values"] = names
        if names:
            self._order_combo.current(0)
            self._on_order_selected()

    # ------------------------------------------------------------------
    # Callbacks vom SorterEngine
    # ------------------------------------------------------------------

    def update_state(self, state: SorterState):
        state_labels = {
            SorterState.IDLE:             ("IDLE",             cfg.THEME_MUTED),
            SorterState.WAITING_FOR_PART: ("Warte auf Teil…",  cfg.THEME_ACCENT),
            SorterState.STOPPING_BELT:    ("Band stoppt…",     cfg.THEME_ACCENT),
            SorterState.SCANNING:         ("Scanne…",          cfg.THEME_WARNING),
            SorterState.SORTING:          ("Sortiere…",        "#a78bfa"),
            SorterState.BELT_RESTART:     ("Band läuft…",      cfg.THEME_ACCENT),
            SorterState.ERROR:            ("FEHLER",           cfg.THEME_DANGER),
            SorterState.PAUSED:           ("PAUSIERT",         cfg.THEME_MUTED),
        }
        text, color = state_labels.get(state, (str(state.name), cfg.THEME_TEXT))
        self._lbl_state.configure(text=text, foreground=color)

    def update_part(self, part_num, name, score, container, color_name=""):
        color_suffix = f" ({color_name})" if color_name else ""
        self._lbl_part.configure(
            text=f"{part_num} – {name}{color_suffix}  ({score:.0%})")
        self._lbl_container.configure(
            text=f"Behälter {container}")
