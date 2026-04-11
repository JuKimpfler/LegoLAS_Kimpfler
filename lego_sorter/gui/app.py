"""
LegoLAS Hauptfenster (tkinter).

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  Toolbar: Logo | Tab-Buttons         [STOP] [✕ Beenden] │
  ├─────────────────────────────────────────────────────────┤
  │                                                          │
  │            Aktive View (wechselnd)                       │
  │                                                          │
  ├─────────────────────────────────────────────────────────┤
  │  Statusleiste: Zustand  |  Version                       │
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
from typing import Optional

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

# Tabs: key → (icon, Bezeichnung, Tastenkürzel)
_TABS = [
    ("sort",        "🔀", "Sortieren",     "F2"),
    ("calibration", "⚙️", "Kalibrierung",  "F3"),
    ("settings",    "🛠", "Einstellungen", "F4"),
    ("database",    "📊", "Datenbank",     "F5"),
]

# View-Klassen (lazy initialization)
_VIEW_CLASSES = {
    "sort":        SortView,
    "calibration": CalibrationView,
    "settings":    SettingsView,
    "database":    DatabaseView,
}


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

        # Coalesced engine-callback state (set from worker thread, flushed in UI thread)
        self._pending_state_update: Optional[SorterState] = None
        self._state_cb_pending: bool = False
        self._pending_part_update: Optional[tuple] = None
        self._part_cb_pending: bool = False

        # ------------------------------------------------------------------
        # Hardware / Core Initialisierung
        # ------------------------------------------------------------------
        self.gpio  = GPIOController(cfg)
        self.gpio.setup()

        self.camera = CameraManager(cfg)
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
        self._build_statusbar()
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
        self._toolbar = tk.Frame(
            self, bg=cfg.THEME_SURFACE,
            height=cfg.TOOLBAR_HEIGHT)
        self._toolbar.pack(side="top", fill="x")
        self._toolbar.pack_propagate(False)

        # Vertikaler Trennstreifen unten (Akzentlinie)
        tk.Frame(self, bg=cfg.THEME_ACCENT, height=2).pack(
            side="top", fill="x")

        # Logo / Titel
        tk.Label(
            self._toolbar,
            text="🧱 LegoLAS",
            bg=cfg.THEME_SURFACE,
            fg=cfg.THEME_ACCENT,
            font=(cfg.FONT_TITLE[0], 13, "bold"),
        ).pack(side="left", padx=(16, 8))

        # Dünne vertikale Trennlinie nach Logo
        tk.Frame(self._toolbar, bg=cfg.THEME_BORDER,
                 width=1).pack(side="left", fill="y", pady=8, padx=4)

        # Tab-Buttons
        self._tab_buttons = {}
        for key, icon, label, shortcut in _TABS:
            btn = tk.Button(
                self._toolbar,
                text=f"{icon}  {label}",
                bg=cfg.THEME_SURFACE,
                fg=cfg.THEME_MUTED,
                activebackground=cfg.THEME_SURFACE2,
                activeforeground=cfg.THEME_TEXT,
                relief="flat",
                bd=0,
                font=cfg.FONT_BODY,
                padx=14,
                pady=0,
                cursor="hand2",
                command=lambda k=key: self._show_view(k),
            )
            btn.pack(side="left", fill="y", padx=1)
            self._tab_buttons[key] = btn

        # Notfall-Stop (rechts)
        tk.Button(
            self._toolbar,
            text="⏹  STOP",
            bg=cfg.THEME_DANGER,
            fg=cfg.THEME_TEXT,
            activebackground="#dc2626",
            activeforeground=cfg.THEME_TEXT,
            relief="flat",
            bd=0,
            font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
            padx=14,
            cursor="hand2",
            command=self._emergency_stop,
        ).pack(side="right", padx=(4, 16), fill="y", pady=8)

        # Beenden
        tk.Button(
            self._toolbar,
            text="✕  Beenden",
            bg=cfg.THEME_SURFACE,
            fg=cfg.THEME_MUTED,
            activebackground=cfg.THEME_DANGER,
            activeforeground=cfg.THEME_TEXT,
            relief="flat",
            bd=0,
            font=cfg.FONT_BODY,
            padx=12,
            cursor="hand2",
            command=self._on_close,
        ).pack(side="right", fill="y", pady=8, padx=2)

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    def _build_views(self):
        self._container = ttk.Frame(self)
        self._container.pack(fill="both", expand=True)
        self._container.rowconfigure(0, weight=1)
        self._container.columnconfigure(0, weight=1)

        # Views werden erst beim ersten Zugriff erstellt (lazy initialization).
        self._views: dict = {}
        self._current_view_key = None

    def _get_or_create_view(self, key: str):
        """Erstellt eine View beim ersten Zugriff und gibt sie zurück."""
        if key not in self._views:
            cls = _VIEW_CLASSES.get(key)
            if cls is None:
                return None
            view = cls(self._container, self)
            view.grid(row=0, column=0, sticky="nsew")
            self._views[key] = view
        return self._views[key]

    def _show_view(self, key: str):
        if self._current_view_key == key:
            return
        # Alte View ausblenden
        prev_key = self._current_view_key
        if prev_key:
            old_view = self._views.get(prev_key)
            if old_view:
                old_view.on_hide()

        # Neue View holen/erstellen und nach vorne bringen
        view = self._get_or_create_view(key)
        if view:
            view.tkraise()
            view.on_show()
            self._current_view_key = key

        # Tab-Button hervorheben – nur die zwei betroffenen Buttons ändern
        if prev_key:
            old_btn = self._tab_buttons.get(prev_key)
            if old_btn:
                old_btn.configure(
                    bg=cfg.THEME_SURFACE,
                    fg=cfg.THEME_MUTED,
                    font=cfg.FONT_BODY)
        new_btn = self._tab_buttons.get(key)
        if new_btn:
            new_btn.configure(
                bg=cfg.THEME_ACCENT,
                fg=cfg.THEME_BG,
                font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"))

        # Statusleiste aktualisieren
        tab_label = next(
            (lbl for k, _, lbl, _ in _TABS if k == key), key)
        self._statusbar_view_lbl.configure(text=f"  {tab_label}")

    # ------------------------------------------------------------------
    # Statusleiste
    # ------------------------------------------------------------------

    def _build_statusbar(self):
        # Dünne Trennlinie oben
        tk.Frame(self, bg=cfg.THEME_BORDER, height=1).pack(
            side="bottom", fill="x")

        bar = tk.Frame(self, bg=cfg.THEME_SURFACE, height=26)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        self._statusbar_view_lbl = tk.Label(
            bar, text="", bg=cfg.THEME_SURFACE,
            fg=cfg.THEME_MUTED, font=cfg.FONT_SMALL, anchor="w")
        self._statusbar_view_lbl.pack(side="left")

        tk.Label(
            bar, text="LegoLAS  •  Raspberry Pi",
            bg=cfg.THEME_SURFACE, fg=cfg.THEME_MUTED,
            font=cfg.FONT_SMALL, anchor="e",
        ).pack(side="right", padx=10)

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
    # Coalescing: mehrfache Aufrufe innerhalb einer Event-Loop-Iteration
    # werden zu einem einzigen UI-Update zusammengefasst.
    # ------------------------------------------------------------------

    def _on_engine_state(self, state: SorterState):
        self._pending_state_update = state
        if not self._state_cb_pending:
            self._state_cb_pending = True
            self.after(0, self._flush_state_update)

    def _flush_state_update(self):
        self._state_cb_pending = False
        state = self._pending_state_update
        self._pending_state_update = None
        if state is not None:
            self._update_sort_view_state(state)

    def _on_part_identified(self, part_num, name, score, container,
                             color_name=""):
        self._pending_part_update = (part_num, name, score, container,
                                     color_name)
        if not self._part_cb_pending:
            self._part_cb_pending = True
            self.after(0, self._flush_part_update)

    def _flush_part_update(self):
        self._part_cb_pending = False
        data = self._pending_part_update
        self._pending_part_update = None
        if data is not None:
            self._update_sort_view_part(*data)

    def _on_part_unknown(self, container):
        self._pending_part_update = ("???", "Unbekannt", 0.0, container, "")
        if not self._part_cb_pending:
            self._part_cb_pending = True
            self.after(0, self._flush_part_update)

    def _update_sort_view_state(self, state: SorterState):
        view = self._views.get("sort")
        if view:
            view.update_state(state)

    def _update_sort_view_part(self, part_num, name, score, container,
                                color_name=""):
        view = self._views.get("sort")
        if view:
            view.update_part(part_num, name, score, container, color_name)

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
