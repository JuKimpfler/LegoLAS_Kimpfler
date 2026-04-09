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
    """Wendet den dunklen LegoLAS-Theme auf ein tk.Tk-Fenster an."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY,
                    borderwidth=0,
                    relief="flat")

    style.configure("TFrame",
                    background=cfg.THEME_BG)
    style.configure("Surface.TFrame",
                    background=cfg.THEME_SURFACE)
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
    style.configure("Surface.TLabel",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY)
    style.configure("TButton",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    font=cfg.FONT_BODY,
                    padding=(12, 6),
                    relief="flat",
                    borderwidth=1)
    style.map("TButton",
              background=[("active", cfg.THEME_ACCENT),
                          ("pressed", cfg.THEME_ACCENT)],
              foreground=[("active", cfg.THEME_BG),
                          ("pressed", cfg.THEME_BG)])
    style.configure("Accent.TButton",
                    background=cfg.THEME_ACCENT,
                    foreground=cfg.THEME_BG,
                    font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"),
                    padding=(12, 6))
    style.map("Accent.TButton",
              background=[("active", "#79c0ff"), ("pressed", "#79c0ff")])
    style.configure("Danger.TButton",
                    background=cfg.THEME_DANGER,
                    foreground=cfg.THEME_BG,
                    font=cfg.FONT_BODY,
                    padding=(12, 6))
    style.map("Danger.TButton",
              background=[("active", "#ff7b72")])
    style.configure("Success.TButton",
                    background=cfg.THEME_ACCENT2,
                    foreground=cfg.THEME_BG,
                    font=cfg.FONT_BODY,
                    padding=(12, 6))
    style.map("Success.TButton",
              background=[("active", "#56d364")])
    style.configure("TNotebook",
                    background=cfg.THEME_BG,
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    padding=[16, 6])
    style.map("TNotebook.Tab",
              background=[("selected", cfg.THEME_ACCENT)],
              foreground=[("selected", cfg.THEME_BG)])
    style.configure("TScale",
                    background=cfg.THEME_BG,
                    troughcolor=cfg.THEME_SURFACE)
    style.configure("TProgressbar",
                    background=cfg.THEME_ACCENT,
                    troughcolor=cfg.THEME_SURFACE)
    style.configure("Treeview",
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    fieldbackground=cfg.THEME_SURFACE,
                    rowheight=28)
    style.configure("Treeview.Heading",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_ACCENT,
                    font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold"))
    style.map("Treeview",
              background=[("selected", cfg.THEME_ACCENT)],
              foreground=[("selected", cfg.THEME_BG)])
    style.configure("TScrollbar",
                    background=cfg.THEME_SURFACE,
                    troughcolor=cfg.THEME_BG,
                    arrowcolor=cfg.THEME_MUTED)
    style.configure("TCombobox",
                    fieldbackground=cfg.THEME_SURFACE,
                    background=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    selectbackground=cfg.THEME_ACCENT)
    style.configure("TEntry",
                    fieldbackground=cfg.THEME_SURFACE,
                    foreground=cfg.THEME_TEXT,
                    insertcolor=cfg.THEME_TEXT)
    style.configure("TCheckbutton",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT)
    style.configure("TRadiobutton",
                    background=cfg.THEME_BG,
                    foreground=cfg.THEME_TEXT)
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
