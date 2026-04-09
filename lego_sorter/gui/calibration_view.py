"""
Kalibrierungsansicht für LegoLAS GUI.

Erlaubt:
  - Servo manuell in Grad verstellen (+/- Buttons)
  - Aktuelle Position als Slot 1–6 speichern
  - Alle Positionen in der Datenbank überschreiben
  - Live-Anzeige des aktuellen Winkels
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from .base import BaseView


class CalibrationView(BaseView):

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Titel
        ttk.Label(self, text="⚙️  Servo-Kalibrierung",
                  style="Title.TLabel").grid(
            row=0, column=0, pady=(16, 4), sticky="n")
        ttk.Label(self,
                  text="Stellen Sie den Servo auf die gewünschte Position "
                       "und speichern Sie diese für jeden Behälter.",
                  style="Muted.TLabel",
                  justify="center").grid(row=1, column=0, pady=(0, 8))

        # Scroll-fähiger Hauptbereich
        outer = ttk.Frame(self, style="TFrame")
        outer.grid(row=2, column=0, sticky="nsew", padx=32, pady=4)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)

        # ── Linke Spalte: Steuerung ────────────────────────────────────────
        ctrl = ttk.Frame(outer, style="Surface.TFrame")
        ctrl.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        ctrl.columnconfigure(0, weight=1)

        # Aktueller Winkel – große Anzeige
        ttk.Label(ctrl, text="Aktueller Winkel",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        self._angle_var = tk.DoubleVar(value=0.0)
        self._lbl_angle = ttk.Label(ctrl,
                                    text="0.0 °",
                                    foreground=cfg.THEME_ACCENT,
                                    background=cfg.THEME_SURFACE,
                                    font=(cfg.FONT_BODY[0], 26, "bold"))
        self._lbl_angle.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=2, column=0, sticky="ew", padx=12, pady=4)

        # Direkte Eingabe per Slider
        ttk.Label(ctrl, text="Direkteingabe:",
                  style="Surface.TLabel").grid(
            row=3, column=0, padx=16, pady=(10, 2), sticky="w")
        self._slider = ttk.Scale(ctrl, from_=0, to=180,
                                 orient="horizontal",
                                 variable=self._angle_var,
                                 command=self._on_slider)
        self._slider.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="ew")

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=5, column=0, sticky="ew", padx=12, pady=4)

        # Grob-Schritte
        ttk.Label(ctrl, text="Grob  (±10°):",
                  style="Surface.TLabel").grid(
            row=6, column=0, padx=16, pady=(10, 2), sticky="w")
        step_frm_coarse = ttk.Frame(ctrl, style="Surface.TFrame")
        step_frm_coarse.grid(row=7, column=0, padx=16, pady=(0, 4), sticky="ew")
        step_frm_coarse.columnconfigure((0, 1), weight=1)
        ttk.Button(step_frm_coarse, text="−10",
                   command=lambda: self._step(-10)).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")
        ttk.Button(step_frm_coarse, text="+10",
                   command=lambda: self._step(10)).grid(
            row=0, column=1, padx=(4, 0), sticky="ew")

        # Fein-Schritte
        ttk.Label(ctrl, text="Fein  (±1°):",
                  style="Surface.TLabel").grid(
            row=8, column=0, padx=16, pady=(8, 2), sticky="w")
        step_frm_fine = ttk.Frame(ctrl, style="Surface.TFrame")
        step_frm_fine.grid(row=9, column=0, padx=16, pady=(0, 10), sticky="ew")
        step_frm_fine.columnconfigure((0, 1), weight=1)
        ttk.Button(step_frm_fine, text="−1",
                   command=lambda: self._step(-1)).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")
        ttk.Button(step_frm_fine, text="+1",
                   command=lambda: self._step(1)).grid(
            row=0, column=1, padx=(4, 0), sticky="ew")

        ttk.Separator(ctrl, orient="horizontal").grid(
            row=10, column=0, sticky="ew", padx=12, pady=4)

        # Home-Button
        ttk.Button(ctrl, text="🏠  Startposition (0°)",
                   command=self._go_home,
                   style="TButton").grid(
            row=11, column=0, padx=16, pady=(8, 16), sticky="ew")

        # ── Rechte Spalte: Slots ──────────────────────────────────────────
        slots_panel = ttk.Frame(outer, style="Surface.TFrame")
        slots_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        slots_panel.columnconfigure(0, weight=1)

        ttk.Label(slots_panel,
                  text="Position als Slot speichern",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        slot_grid = ttk.Frame(slots_panel, style="Surface.TFrame")
        slot_grid.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        for i in range(3):
            slot_grid.columnconfigure(i, weight=1)
        for i in range(1, 7):
            r, c = divmod(i - 1, 3)
            ttk.Button(slot_grid, text=f"Slot {i}",
                       command=lambda n=i: self._save_slot(n),
                       style="Accent.TButton").grid(
                row=r, column=c, padx=4, pady=4, sticky="ew")

        ttk.Separator(slots_panel, orient="horizontal").grid(
            row=2, column=0, sticky="ew", padx=12, pady=4)

        ttk.Label(slots_panel, text="Gespeicherte Positionen",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=3, column=0, padx=16, pady=(8, 4), sticky="w")

        tree_frm = ttk.Frame(slots_panel, style="Surface.TFrame")
        tree_frm.grid(row=4, column=0, padx=16, pady=(0, 8), sticky="nsew")
        tree_frm.columnconfigure(0, weight=1)
        slots_panel.rowconfigure(4, weight=1)

        self._tree = ttk.Treeview(tree_frm, columns=("slot", "angle"),
                                   show="headings", height=7)
        self._tree.heading("slot",  text="Slot")
        self._tree.heading("angle", text="Winkel (°)")
        self._tree.column("slot",  width=80,  anchor="center")
        self._tree.column("angle", width=110, anchor="center")
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frm, orient="vertical",
                           command=self._tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=sb.set)

        ttk.Button(slots_panel,
                   text="→ Auf gespeicherten Slot fahren",
                   command=self._goto_slot,
                   style="TButton").grid(
            row=5, column=0, padx=16, pady=(4, 16), sticky="ew")

        self._refresh_table()

    # ------------------------------------------------------------------
    # Steuerung
    # ------------------------------------------------------------------

    def _step(self, delta: float):
        new_angle = max(0, min(180, self._angle_var.get() + delta))
        self._angle_var.set(new_angle)
        self._apply_angle(new_angle)

    def _on_slider(self, _value=None):
        angle = self._angle_var.get()
        self._apply_angle(angle)

    def _apply_angle(self, angle: float):
        self._lbl_angle.configure(text=f"{angle:.1f} °")
        gpio = self.app.gpio
        if gpio:
            gpio.servo_set_angle(angle)

    def _go_home(self):
        self._angle_var.set(0)
        self._apply_angle(0)

    def _save_slot(self, slot: int):
        angle = self._angle_var.get()
        db = self.app.db
        if db:
            db.set_servo_position(slot, angle)
            self._refresh_table()
            messagebox.showinfo(
                "Gespeichert",
                f"Slot {slot} → {angle:.1f}° gespeichert.",
                parent=self,
            )

    def _goto_slot(self):
        sel = self._tree.selection()
        if not sel:
            return
        slot = int(self._tree.item(sel[0])["values"][0])
        db = self.app.db
        if not db:
            return
        positions = db.get_servo_positions()
        angle = positions.get(slot, 0)
        self._angle_var.set(angle)
        self._apply_angle(angle)

    # ------------------------------------------------------------------
    # Tabelle aktualisieren
    # ------------------------------------------------------------------

    def _refresh_table(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        db = self.app.db
        if not db:
            return
        for slot, angle in sorted(db.get_servo_positions().items()):
            self._tree.insert("", "end", values=(slot, f"{angle:.1f}°"))

    def on_show(self):
        self._refresh_table()
