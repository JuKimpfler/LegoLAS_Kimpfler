"""
Sortier-Ansicht für LegoLAS GUI.

Enthält:
  - Live-Kameravorschau
  - Status-Panel (Zustand, letztes Teil, Behälter)
  - Manuelle Steuerung (Band, Scan, Weiche)
  - Umschaltung Manuell / Automatik
  - Umschaltung Sortiermodus / Auftragsmodus

Tastaturkürzel:
  B        – Band an/aus
  Space    – Manuell scannen
  A        – Auto-Modus an/aus
  1–6      – Weiche manuell stellen
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from core.sorter_engine import SorterState, SortMode
from .base import BaseView

try:
    from PIL import ImageTk
    _PIL = True
except ImportError:
    _PIL = False


class SortView(BaseView):

    def _build_ui(self):
        self._last_frame_counter = -1  # Change-Detection für Kamera-Update
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # ---- Linke Seite: Kamera ----
        cam_frame = ttk.Frame(self, style="Surface.TFrame")
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        cam_frame.rowconfigure(1, weight=1)
        cam_frame.columnconfigure(0, weight=1)

        ttk.Label(cam_frame, text="📷  Live-Kamera",
                  style="Title.TLabel").grid(row=0, column=0, pady=(8, 4))

        self._cam_label = tk.Label(cam_frame, bg=cfg.THEME_SURFACE,
                                   text="Kamera wird initialisiert…",
                                   fg=cfg.THEME_MUTED,
                                   font=cfg.FONT_BODY)
        self._cam_label.grid(row=1, column=0, sticky="nsew",
                              padx=8, pady=(0, 8))

        # ---- Rechte Seite: Steuerung ----
        ctrl_frame = ttk.Frame(self, style="TFrame")
        ctrl_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ctrl_frame.columnconfigure(0, weight=1)

        self._build_status(ctrl_frame)
        self._build_mode_switcher(ctrl_frame)
        self._build_manual_controls(ctrl_frame)
        self._build_container_buttons(ctrl_frame)

        # Live-Update starten
        self._update_camera()

    # ------------------------------------------------------------------
    # Status-Panel
    # ------------------------------------------------------------------

    def _build_status(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Zustand:", style="Surface.TLabel").grid(
            row=0, column=0, padx=8, pady=4, sticky="w")
        self._lbl_state = ttk.Label(frm, text="IDLE",
                                    style="Surface.TLabel",
                                    foreground=cfg.THEME_ACCENT)
        self._lbl_state.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Letztes Teil:", style="Surface.TLabel").grid(
            row=1, column=0, padx=8, pady=4, sticky="w")
        self._lbl_part = ttk.Label(frm, text="–",
                                   style="Surface.TLabel",
                                   wraplength=200)
        self._lbl_part.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Behälter:", style="Surface.TLabel").grid(
            row=2, column=0, padx=8, pady=4, sticky="w")
        self._lbl_container = ttk.Label(frm, text="–",
                                        style="Surface.TLabel",
                                        foreground=cfg.THEME_ACCENT2)
        self._lbl_container.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Sensor:", style="Surface.TLabel").grid(
            row=3, column=0, padx=8, pady=4, sticky="w")
        self._lbl_sensor = ttk.Label(frm, text="frei",
                                     style="Surface.TLabel")
        self._lbl_sensor.grid(row=3, column=1, padx=8, pady=4, sticky="w")

    # ------------------------------------------------------------------
    # Moduswahl
    # ------------------------------------------------------------------

    def _build_mode_switcher(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        frm.columnconfigure((0, 1), weight=1)

        # Manuell / Auto
        self._auto_var = tk.BooleanVar(value=False)
        ttk.Label(frm, text="Betrieb:", style="Surface.TLabel").grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")
        ttk.Radiobutton(frm, text="Manuell  [F2]",
                        variable=self._auto_var, value=False,
                        command=self._on_mode_change,
                        style="TRadiobutton").grid(
            row=1, column=0, padx=8, pady=2, sticky="w")
        ttk.Radiobutton(frm, text="Automatik  [A]",
                        variable=self._auto_var, value=True,
                        command=self._on_mode_change,
                        style="TRadiobutton").grid(
            row=1, column=1, padx=8, pady=2, sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        # Sortier / Auftrag
        self._sort_mode_var = tk.StringVar(value="sort")
        ttk.Label(frm, text="Modus:", style="Surface.TLabel").grid(
            row=3, column=0, columnspan=2, padx=8, pady=(4, 4), sticky="w")
        ttk.Radiobutton(frm, text="Sortiermodus",
                        variable=self._sort_mode_var, value="sort",
                        command=self._on_sort_mode_change,
                        style="TRadiobutton").grid(
            row=4, column=0, padx=8, pady=2, sticky="w")
        ttk.Radiobutton(frm, text="Auftragsmodus",
                        variable=self._sort_mode_var, value="order",
                        command=self._on_sort_mode_change,
                        style="TRadiobutton").grid(
            row=4, column=1, padx=8, pady=2, sticky="w")

        # Auftrag-Auswahl
        ttk.Label(frm, text="Aktiver Auftrag:",
                  style="Surface.TLabel").grid(
            row=5, column=0, padx=8, pady=(4, 2), sticky="w")
        self._order_var = tk.StringVar(value="")
        self._order_combo = ttk.Combobox(frm, textvariable=self._order_var,
                                          state="readonly", width=18)
        self._order_combo.grid(row=5, column=1, padx=8, pady=2, sticky="ew")
        self._order_combo.bind("<<ComboboxSelected>>", self._on_order_selected)
        self._refresh_order_list()

    # ------------------------------------------------------------------
    # Manuelle Steuerung
    # ------------------------------------------------------------------

    def _build_manual_controls(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        frm.columnconfigure((0, 1), weight=1)

        ttk.Label(frm, text="Manuelle Steuerung",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 6))

        self._btn_belt = ttk.Button(frm, text="▶  Band starten  [B]",
                                    command=self._toggle_belt,
                                    style="Accent.TButton")
        self._btn_belt.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        ttk.Button(frm, text="📷  Scannen  [Space]",
                   command=self._manual_scan,
                   style="TButton").grid(
            row=1, column=1, padx=8, pady=4, sticky="ew")

    # ------------------------------------------------------------------
    # Behälter-Schnellauswahl
    # ------------------------------------------------------------------

    def _build_container_buttons(self, parent):
        frm = ttk.Frame(parent, style="Surface.TFrame")
        frm.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        for i in range(6):
            frm.columnconfigure(i, weight=1)

        ttk.Label(frm, text="Weiche stellen  [1–6]:",
                  style="Surface.TLabel").grid(
            row=0, column=0, columnspan=6, padx=8, pady=(8, 4), sticky="w")

        for i in range(1, 7):
            ttk.Button(frm, text=str(i),
                       command=lambda n=i: self._set_container(n),
                       style="TButton").grid(
                row=1, column=i - 1, padx=4, pady=4, sticky="ew")

    # ------------------------------------------------------------------
    # Kamera-Update
    # ------------------------------------------------------------------

    def _update_camera(self):
        if not self.winfo_exists():
            return
        cam = self.app.camera
        if cam and cam.is_open and _PIL:
            current_counter = cam.frame_counter
            if current_counter != self._last_frame_counter:
                # Nur verarbeiten wenn tatsächlich ein neuer Frame vorliegt
                self._last_frame_counter = current_counter
                w = self._cam_label.winfo_width() or 400
                h = self._cam_label.winfo_height() or 300
                if w < 10:
                    w, h = 400, 300
                img = cam.get_pil_image(width=w, height=h)
                if img:
                    photo = ImageTk.PhotoImage(img)
                    self._cam_label.configure(image=photo, text="")
                    self._cam_label.image = photo  # Referenz halten

        # Sensor-Status aktualisieren
        gpio = self.app.gpio
        if gpio:
            detected = gpio.sensor_read()
            if detected:
                self._lbl_sensor.configure(
                    text="◉ TEIL ERKANNT",
                    foreground=cfg.THEME_DANGER)
            else:
                self._lbl_sensor.configure(
                    text="○ frei",
                    foreground=cfg.THEME_ACCENT2)

        self.after(int(1000 / cfg.LIVE_FPS), self._update_camera)

    # ------------------------------------------------------------------
    # Event-Handler
    # ------------------------------------------------------------------

    def _toggle_belt(self):
        gpio = self.app.gpio
        if not gpio:
            return
        if gpio.belt_running:
            gpio.belt_stop()
            self._btn_belt.configure(text="▶  Band starten  [B]")
        else:
            gpio.belt_start()
            self._btn_belt.configure(text="⏹  Band stoppen  [B]")

    def _manual_scan(self):
        engine = self.app.engine
        if not engine:
            return
        result = engine.manual_scan()
        if result:
            self._lbl_part.configure(
                text=f"{result['part_num']}  {result['name']}  "
                     f"({result['score']:.0%})")
            self._lbl_container.configure(
                text=f"Behälter {result['container']}")
        else:
            self._lbl_part.configure(text="Nicht erkannt")
            self._lbl_container.configure(
                text=f"Behälter {engine.FALLBACK_CONTAINER}")

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
            SorterState.IDLE:             ("IDLE",              cfg.THEME_MUTED),
            SorterState.WAITING_FOR_PART: ("Warte auf Teil…",   cfg.THEME_ACCENT),
            SorterState.STOPPING_BELT:    ("Band stoppt…",      cfg.THEME_ACCENT),
            SorterState.SCANNING:         ("Scanne…",           "#f9e2af"),
            SorterState.SORTING:          ("Sortiere…",         "#cba6f7"),
            SorterState.BELT_RESTART:     ("Band läuft…",       cfg.THEME_ACCENT),
            SorterState.ERROR:            ("FEHLER",            cfg.THEME_DANGER),
            SorterState.PAUSED:           ("PAUSIERT",          cfg.THEME_MUTED),
        }
        text, color = state_labels.get(state, (str(state.name), cfg.THEME_TEXT))
        self._lbl_state.configure(text=text, foreground=color)

    def update_part(self, part_num, name, score, container):
        self._lbl_part.configure(
            text=f"{part_num}  {name}  ({score:.0%})")
        self._lbl_container.configure(
            text=f"Behälter {container}")

    def on_show(self):
        self._refresh_order_list()

    def on_hide(self):
        pass
