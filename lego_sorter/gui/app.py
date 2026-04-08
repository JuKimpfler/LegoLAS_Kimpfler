"""
LegoLAS Hauptfenster (tkinter).

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  Toolbar: Tab-Buttons  [Sortieren|Kalibrierung|...]      │
  ├─────────────────────────────────────────────────────────┤
  │                                                          │
  │            Aktive View (wechselnd)                       │
  │                                                          │
  └─────────────────────────────────────────────────────────┘

Tastaturkürzel:
  F2       – Sortier-/Manuelansicht
  F3       – Kalibrierung
  F4       – Einstellungen
  F5       – Datenbank
  Escape   – Beenden (mit Bestätigung)
  B        – Band an/aus (wenn SortView aktiv)
  Space    – Manuell scannen (wenn SortView aktiv)
  1–6      – Weiche stellen (wenn SortView aktiv)
  A        – Auto-Modus an/aus (wenn SortView aktiv)
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox

# Pfad-Anpassung
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as cfg

from hardware.gpio_controller import GPIOController
from hardware.camera_manager  import CameraManager
from core.brickognize          import BrickognizeClient
from core.database             import Database
from core.order_manager        import OrderManager
from core.sorter_engine        import SorterEngine, SorterState

from .base             import apply_theme
from .sort_view        import SortView
from .calibration_view import CalibrationView
from .settings_view    import SettingsView
from .database_view    import DatabaseView

logger = logging.getLogger(__name__)


class LegoLASApp(tk.Tk):
    """
    Hauptanwendungsklasse.
    Initialisiert alle Hardware- und Core-Komponenten,
    erstellt das Hauptfenster und verwaltet die View-Umschaltung.
    """

    def __init__(self):
        super().__init__()
        self.title(cfg.WINDOW_TITLE)
        self.attributes("-fullscreen", True)
        self.resizable(True, True)
        apply_theme(self)

        # ------------------------------------------------------------------
        # Shared State
        # ------------------------------------------------------------------
        self.active_order_id: int = None

        # ------------------------------------------------------------------
        # Hardware / Core Initialisierung
        # ------------------------------------------------------------------
        self.gpio  = GPIOController(cfg)
        self.gpio.setup()

        self.camera = CameraManager(cfg, use_droidcam=False)
        self.camera.start()

        self.api = BrickognizeClient(cfg)

        os.makedirs(cfg.DATA_DIR,    exist_ok=True)
        os.makedirs(cfg.ORDERS_DIR,  exist_ok=True)
        os.makedirs(cfg.EXPORTS_DIR, exist_ok=True)
        self.db = Database(cfg.DB_PATH, cfg)

        self.order_manager = OrderManager(cfg.ORDERS_DIR, cfg.EXPORTS_DIR)

        self.engine = SorterEngine(
            self.gpio, self.camera, self.api, self.db, cfg)
        self.engine.on_state_change    = self._on_engine_state
        self.engine.on_part_identified = self._on_part_identified
        self.engine.on_part_unknown    = self._on_part_unknown

        # Gespeicherte Einstellungen laden
        self._load_settings()

        # ------------------------------------------------------------------
        # GUI aufbauen
        # ------------------------------------------------------------------
        self._build_toolbar()
        self._build_views()
        self._register_keybindings()

        # Startview: Sortieren
        self._show_view("sort")

        # Fenster-Schließen abfangen
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("LegoLASApp gestartet.")

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        self._toolbar = tk.Frame(self, bg=cfg.THEME_SURFACE, height=50)
        self._toolbar.pack(side="top", fill="x")
        self._toolbar.pack_propagate(False)

        # Logo / Titel
        tk.Label(self._toolbar,
                 text="🧱 LegoLAS",
                 bg=cfg.THEME_SURFACE,
                 fg=cfg.THEME_ACCENT,
                 font=(cfg.FONT_TITLE[0], 14, "bold")).pack(
            side="left", padx=16)

        # Tab-Buttons (rechts vom Logo)
        self._tab_buttons = {}
        tabs = [
            ("sort",        "🔀  Sortieren  [F2]"),
            ("calibration", "⚙️  Kalibrierung  [F3]"),
            ("settings",    "🛠  Einstellungen  [F4]"),
            ("database",    "📊  Datenbank  [F5]"),
        ]
        for key, label in tabs:
            btn = tk.Button(
                self._toolbar,
                text=label,
                bg=cfg.THEME_SURFACE,
                fg=cfg.THEME_TEXT,
                activebackground=cfg.THEME_ACCENT,
                activeforeground=cfg.THEME_BG,
                relief="flat",
                font=cfg.FONT_BODY,
                padx=12, pady=8,
                command=lambda k=key: self._show_view(k),
            )
            btn.pack(side="left", padx=2)
            self._tab_buttons[key] = btn

        # Notfall-Stop
        tk.Button(
            self._toolbar,
            text="⏹  STOP",
            bg=cfg.THEME_DANGER,
            fg=cfg.THEME_BG,
            activebackground="#eba0ac",
            relief="flat",
            font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
            padx=12, pady=8,
            command=self._emergency_stop,
        ).pack(side="right", padx=16)

        # Beenden
        tk.Button(
            self._toolbar,
            text="✕  Beenden",
            bg=cfg.THEME_SURFACE,
            fg=cfg.THEME_MUTED,
            activebackground=cfg.THEME_DANGER,
            activeforeground=cfg.THEME_BG,
            relief="flat",
            font=cfg.FONT_BODY,
            padx=12, pady=8,
            command=self._on_close,
        ).pack(side="right", padx=4)

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    def _build_views(self):
        self._container = ttk.Frame(self)
        self._container.pack(fill="both", expand=True)
        self._container.rowconfigure(0, weight=1)
        self._container.columnconfigure(0, weight=1)

        self._views = {
            "sort":        SortView(self._container, self),
            "calibration": CalibrationView(self._container, self),
            "settings":    SettingsView(self._container, self),
            "database":    DatabaseView(self._container, self),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self._current_view_key = None

    def _show_view(self, key: str):
        if self._current_view_key == key:
            return
        # Alte View ausblenden
        if self._current_view_key:
            old_view = self._views.get(self._current_view_key)
            if old_view:
                old_view.on_hide()

        # Neue View nach oben bringen
        view = self._views.get(key)
        if view:
            view.tkraise()
            view.on_show()
            self._current_view_key = key

        # Tab-Button hervorheben
        for k, btn in self._tab_buttons.items():
            if k == key:
                btn.configure(bg=cfg.THEME_ACCENT,
                              fg=cfg.THEME_BG)
            else:
                btn.configure(bg=cfg.THEME_SURFACE,
                              fg=cfg.THEME_TEXT)

    # ------------------------------------------------------------------
    # Tastaturkürzel
    # ------------------------------------------------------------------

    def _register_keybindings(self):
        bindings = {
            "<F2>":            lambda e: self._show_view("sort"),
            "<F3>":            lambda e: self._show_view("calibration"),
            "<F4>":            lambda e: self._show_view("settings"),
            "<F5>":            lambda e: self._show_view("database"),
            "<Escape>":        lambda e: self._on_close(),
            f"<{cfg.KEY_TOGGLE_BELT}>":
                               lambda e: self._forward_to_sort("_toggle_belt"),
            "<space>":         lambda e: self._forward_to_sort("_manual_scan"),
            "<KeyPress-a>":    lambda e: self._auto_toggle(),
        }
        for i in range(1, 7):
            bindings[f"<KeyPress-{i}>"] = (
                lambda e, n=i: self._forward_to_sort(
                    "_set_container", n))
        for seq, handler in bindings.items():
            self.bind(seq, handler)

    def _forward_to_sort(self, method: str, *args):
        """Leitet Tastendruck an SortView weiter."""
        view = self._views.get("sort")
        if view and hasattr(view, method):
            getattr(view, method)(*args)

    def _auto_toggle(self):
        view = self._views.get("sort")
        if view:
            current = view._auto_var.get()
            view._auto_var.set(not current)
            view._on_mode_change()

    # ------------------------------------------------------------------
    # Engine-Callbacks (aus Worker-Thread → in GUI-Thread dispatchen)
    # ------------------------------------------------------------------

    def _on_engine_state(self, state: SorterState):
        self.after(0, self._update_sort_view_state, state)

    def _on_part_identified(self, part_num, name, score, container):
        self.after(0, self._update_sort_view_part,
                   part_num, name, score, container)

    def _on_part_unknown(self, container):
        self.after(0, self._update_sort_view_part,
                   "???", "Unbekannt", 0.0, container)

    def _update_sort_view_state(self, state: SorterState):
        view = self._views.get("sort")
        if view:
            view.update_state(state)

    def _update_sort_view_part(self, part_num, name, score, container):
        view = self._views.get("sort")
        if view:
            view.update_part(part_num, name, score, container)

    # ------------------------------------------------------------------
    # Hilfsmethoden
    # ------------------------------------------------------------------

    def _emergency_stop(self):
        if self.engine:
            self.engine.stop()
        if self.gpio:
            self.gpio.belt_stop()
        logger.warning("NOT-STOP ausgeführt!")

    def _load_settings(self):
        if not self.db:
            return
        speed = self.db.get_setting("belt_speed", cfg.DEFAULT_BELT_SPEED)
        self.engine.belt_speed = int(speed)
        thresh = self.db.get_setting("conf_threshold",
                                     cfg.DEFAULT_CONF_THRESHOLD)
        self.engine.conf_threshold = float(thresh)

    def _on_close(self):
        if messagebox.askyesno("Beenden",
                               "LegoLAS wirklich beenden?",
                               parent=self):
            logger.info("Anwendung wird beendet.")
            self._emergency_stop()
            self.camera.stop()
            self.gpio.cleanup()
            self.db.close()
            self.destroy()
