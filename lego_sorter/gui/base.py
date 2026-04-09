"""
Basis-Widget für alle LegoLAS-Views.
Stellt Stile, Hilfsmethoden und das gemeinsame Layout-Raster bereit.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Pfad zum lego_sorter-Verzeichnis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


def apply_theme(root: tk.Tk):
    """Wendet den modernen LegoLAS-Theme auf ein tk.Tk-Fenster an."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # ── Basis ──────────────────────────────────────────────────────────────
    style.configure(".",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY,
                    borderwidth=0,
                    relief="flat",
                    focuscolor=cfg.THEME_ACCENT)

    # ── Frames ─────────────────────────────────────────────────────────────
    style.configure("TFrame",       background=cfg.THEME_BG)
    style.configure("Surface.TFrame",  background=cfg.THEME_SURFACE)
    style.configure("Surface2.TFrame", background=cfg.THEME_SURFACE2)

    # ── Labels ─────────────────────────────────────────────────────────────
    style.configure("TLabel",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY)
    style.configure("Title.TLabel",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_ACCENT,
                    font=cfg.FONT_TITLE)
    style.configure("Muted.TLabel",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_MUTED,
                    font=cfg.FONT_BODY)
    style.configure("Small.TLabel",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_MUTED,
                    font=cfg.FONT_SMALL)
    style.configure("Surface.TLabel",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY)
    style.configure("Surface.Muted.TLabel",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_MUTED,
                    font=cfg.FONT_SMALL)

    # ── Buttons (touch-freundlich: min. 44px Höhe durch padding) ───────────
    style.configure("TButton",
                    background=cfg.THEME_SURFACE2,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY,
                    padding=(14, 10),
                    relief="flat",
                    borderwidth=0)
    style.map("TButton",
              background=[("active",  cfg.THEME_ACCENT),
                          ("pressed", cfg.THEME_ACCENT),
                          ("disabled", cfg.THEME_SURFACE)],
              foreground=[("active",  cfg.THEME_BG),
                          ("pressed", cfg.THEME_BG),
                          ("disabled", cfg.THEME_MUTED)])

    style.configure("Accent.TButton",
                    background=cfg.THEME_ACCENT,
                    foreground=cfg.THEME_BG,
                    font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
                    padding=(14, 10))
    style.map("Accent.TButton",
              background=[("active",  "#fbbf24"), ("pressed", "#d97706")])

    style.configure("Danger.TButton",
                    background=cfg.THEME_DANGER,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY,
                    padding=(14, 10))
    style.map("Danger.TButton",
              background=[("active", "#dc2626")])

    style.configure("Success.TButton",
                    background=cfg.THEME_ACCENT2,
                    foreground=cfg.THEME_BG,
                    font=cfg.FONT_BODY,
                    padding=(14, 10))
    style.map("Success.TButton",
              background=[("active", "#059669")])

    # ── Notebook ───────────────────────────────────────────────────────────
    style.configure("TNotebook",
                    background=cfg.THEME_BG,
                    borderwidth=0,
                    tabmargins=[0, 4, 0, 0])
    style.configure("TNotebook.Tab",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_MUTED,
                    padding=[16, 8],
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", cfg.THEME_SURFACE2)],
              foreground=[("selected", cfg.THEME_ACCENT)])

    # ── Skala / Fortschritt ────────────────────────────────────────────────
    style.configure("TScale",
                    background=cfg.THEME_BG,
                    troughcolor=cfg.THEME_SURFACE2,
                    sliderlength=28,
                    sliderrelief="flat")
    style.configure("TProgressbar",
                    background=cfg.THEME_ACCENT,
                    troughcolor=cfg.THEME_SURFACE2,
                    borderwidth=0,
                    thickness=12)

    # ── Treeview ───────────────────────────────────────────────────────────
    style.configure("Treeview",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    fieldbackground=cfg.THEME_SURFACE,
                    rowheight=30,
                    borderwidth=0,
                    relief="flat")
    style.configure("Treeview.Heading",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_ACCENT,
                    font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
                    relief="flat",
                    padding=(8, 6))
    style.map("Treeview",
              background=[("selected", cfg.THEME_ACCENT)],
              foreground=[("selected", cfg.THEME_BG)])

    # ── Scrollbar ──────────────────────────────────────────────────────────
    style.configure("TScrollbar",
                    background=cfg.THEME_SURFACE2,
                    troughcolor=cfg.THEME_BG,
                    arrowcolor=cfg.THEME_MUTED,
                    borderwidth=0,
                    relief="flat",
                    arrowsize=14)
    style.map("TScrollbar",
              background=[("active", cfg.THEME_ACCENT)])

    # ── Eingaben ───────────────────────────────────────────────────────────
    style.configure("TCombobox",
                    fieldbackground=cfg.THEME_SURFACE2,
                    background=cfg.THEME_SURFACE2,
                    foreground=cfg.THEME_TEXT,
                    selectbackground=cfg.THEME_ACCENT,
                    padding=(8, 6),
                    borderwidth=1)
    style.configure("TEntry",
                    fieldbackground=cfg.THEME_SURFACE2,
                    foreground=cfg.THEME_TEXT,
                    insertcolor=cfg.THEME_TEXT,
                    padding=(8, 6),
                    borderwidth=1)

    # ── Checkbutton / Radiobutton ──────────────────────────────────────────
    style.configure("TCheckbutton",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT,
                    focuscolor=cfg.THEME_ACCENT,
                    indicatorcolor=cfg.THEME_SURFACE2)
    style.map("TCheckbutton",
              indicatorcolor=[("selected", cfg.THEME_ACCENT)])
    style.configure("Surface.TCheckbutton",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    focuscolor=cfg.THEME_ACCENT)
    style.map("Surface.TCheckbutton",
              indicatorcolor=[("selected", cfg.THEME_ACCENT)])
    style.configure("TRadiobutton",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT,
                    focuscolor=cfg.THEME_ACCENT,
                    indicatorcolor=cfg.THEME_SURFACE2)
    style.map("TRadiobutton",
              indicatorcolor=[("selected", cfg.THEME_ACCENT)])
    style.configure("Surface.TRadiobutton",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    focuscolor=cfg.THEME_ACCENT)
    style.map("Surface.TRadiobutton",
              indicatorcolor=[("selected", cfg.THEME_ACCENT)])

    # ── Separator ──────────────────────────────────────────────────────────
    style.configure("TSeparator",
                    background=cfg.THEME_BORDER)

    root.configure(bg=cfg.THEME_BG)


class BaseView(ttk.Frame):
    """
    Basisklasse für alle LegoLAS-Ansichten.
    Jede View hat Zugriff auf ``app`` (LegoLASApp-Instanz).
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build_ui()

    def _build_ui(self):
        """Muss von Unterklassen implementiert werden."""
        raise NotImplementedError

    def on_show(self):
        """Wird aufgerufen wenn die View sichtbar wird."""
        pass

    def on_hide(self):
        """Wird aufgerufen wenn die View versteckt wird."""
        pass
