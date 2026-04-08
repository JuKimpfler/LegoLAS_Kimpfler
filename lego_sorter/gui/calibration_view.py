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

        # Titel
        ttk.Label(self, text="⚙️  Servo-Kalibrierung",
                  style="Title.TLabel").grid(
            row=0, column=0, pady=(16, 4), sticky="n")
        ttk.Label(self,
                  text="Stellen Sie den Servo auf die gewünschte Position\n"
                       "und speichern Sie diese für jeden Behälter.",
                  style="Muted.TLabel",
                  justify="center").grid(row=1, column=0, pady=(0, 16))

        # Hauptbereich
        main = ttk.Frame(self, style="Surface.TFrame")
        main.grid(row=2, column=0, padx=40, pady=8, sticky="n")
        main.columnconfigure((0, 1, 2), weight=1)

        # Aktueller Winkel
        ttk.Label(main, text="Aktueller Winkel:",
                  style="Surface.TLabel").grid(
            row=0, column=0, padx=16, pady=12, sticky="e")
        self._angle_var = tk.DoubleVar(value=0.0)
        self._lbl_angle = ttk.Label(main,
                                    text="0.0 °",
                                    foreground=cfg.THEME_ACCENT,
                                    background=cfg.THEME_SURFACE,
                                    font=(cfg.FONT_BODY[0], 22, "bold"))
        self._lbl_angle.grid(row=0, column=1, columnspan=2,
                              padx=16, pady=12, sticky="w")

        ttk.Separator(main, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=8)

        # Grob-Schritte
        ttk.Label(main, text="Grob (±10°):",
                  style="Surface.TLabel").grid(
            row=2, column=0, padx=16, pady=8, sticky="e")
        ttk.Button(main, text="−10",
                   command=lambda: self._step(-10)).grid(
            row=2, column=1, padx=8, pady=8, sticky="ew")
        ttk.Button(main, text="+10",
                   command=lambda: self._step(10)).grid(
            row=2, column=2, padx=8, pady=8, sticky="ew")

        # Fein-Schritte
        ttk.Label(main, text="Fein (±1°):",
                  style="Surface.TLabel").grid(
            row=3, column=0, padx=16, pady=8, sticky="e")
        ttk.Button(main, text="−1",
                   command=lambda: self._step(-1)).grid(
            row=3, column=1, padx=8, pady=8, sticky="ew")
        ttk.Button(main, text="+1",
                   command=lambda: self._step(1)).grid(
            row=3, column=2, padx=8, pady=8, sticky="ew")

        # Slider
        ttk.Label(main, text="Direkte Eingabe:",
                  style="Surface.TLabel").grid(
            row=4, column=0, padx=16, pady=8, sticky="e")
        self._slider = ttk.Scale(main, from_=0, to=180,
                                 orient="horizontal",
                                 variable=self._angle_var,
                                 command=self._on_slider)
        self._slider.grid(row=4, column=1, columnspan=2,
                          padx=8, pady=8, sticky="ew")

        ttk.Separator(main, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", padx=8, pady=4)

        # Slot-Speicher-Buttons
        ttk.Label(main,
                  text="Position als Slot speichern:",
                  style="Surface.TLabel").grid(
            row=6, column=0, padx=16, pady=(8, 4), sticky="e")

        slot_frame = ttk.Frame(main, style="Surface.TFrame")
        slot_frame.grid(row=6, column=1, columnspan=2,
                        padx=8, pady=(8, 4), sticky="ew")
        for i in range(1, 7):
            slot_frame.columnconfigure(i - 1, weight=1)
            ttk.Button(slot_frame, text=f"Slot {i}",
                       command=lambda n=i: self._save_slot(n),
                       style="Accent.TButton").grid(
                row=0, column=i - 1, padx=3, sticky="ew")

        ttk.Separator(main, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky="ew", padx=8, pady=4)

        # Aktuelle Konfiguration anzeigen
        ttk.Label(main, text="Gespeicherte Positionen:",
                  style="Surface.TLabel").grid(
            row=8, column=0, padx=16, pady=(8, 4), sticky="ne")

        self._tree = ttk.Treeview(main, columns=("slot", "angle"),
                                   show="headings", height=7)
        self._tree.heading("slot", text="Slot")
        self._tree.heading("angle", text="Winkel (°)")
        self._tree.column("slot", width=80, anchor="center")
        self._tree.column("angle", width=100, anchor="center")
        self._tree.grid(row=8, column=1, columnspan=2,
                        padx=8, pady=(8, 4), sticky="ew")

        # Auf Slot fahren
        ttk.Button(main, text="→ Auf gespeicherten Slot fahren",
                   command=self._goto_slot).grid(
            row=9, column=1, columnspan=2, padx=8, pady=8, sticky="ew")

        # Home
        ttk.Button(main, text="🏠  Startposition (0°)",
                   command=self._go_home,
                   style="TButton").grid(
            row=10, column=0, columnspan=3, padx=16, pady=8)

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
