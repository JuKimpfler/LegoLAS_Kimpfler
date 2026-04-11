"""
Datenbankansicht für LegoLAS GUI.

Zeigt:
  - Scan-Statistiken (gesamt, je Behälter)
  - Fortschrittsbalken je Behälter (Auftragsmodus)
  - Inventartabelle
  - Scan-Log
  - Reset-Optionen
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from .base import BaseView


class DatabaseView(BaseView):

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Titelzeile + Aktionen-Buttons in einer Reihe
        header = ttk.Frame(self, style="TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="📊  Datenbank & Statistik",
                  style="Title.TLabel").grid(row=0, column=0, sticky="w")

        btn_frm = ttk.Frame(header, style="TFrame")
        btn_frm.grid(row=0, column=1, sticky="e")
        ttk.Button(btn_frm, text="🔄  Aktualisieren",
                   command=self.on_show,
                   style="Accent.TButton").grid(row=0, column=0, padx=(4, 0))
        ttk.Button(btn_frm, text="🗑  Inventar zurücksetzen",
                   command=self._reset_inventory,
                   style="Danger.TButton").grid(row=0, column=1, padx=(8, 0))

        # Notebook
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        self._tab_stats     = ttk.Frame(nb)
        self._tab_progress  = ttk.Frame(nb)
        self._tab_inventory = ttk.Frame(nb)
        self._tab_log       = ttk.Frame(nb)
        nb.add(self._tab_stats,     text="  Statistik  ")
        nb.add(self._tab_progress,  text="  Auftragsfortschritt  ")
        nb.add(self._tab_inventory, text="  Inventar  ")
        nb.add(self._tab_log,       text="  Scan-Log  ")

        self._build_stats()
        self._build_progress()
        self._build_inventory()
        self._build_log()

    # ------------------------------------------------------------------
    # Tab: Statistik
    # ------------------------------------------------------------------

    def _build_stats(self):
        frm = self._tab_stats
        frm.columnconfigure(0, weight=1)

        # Gesamt-Zähler – Hero-Karte
        hero = ttk.Frame(frm, style="Surface.TFrame")
        hero.grid(row=0, column=0, padx=16, pady=16, sticky="ew")
        hero.columnconfigure(0, weight=1)

        self._lbl_total = ttk.Label(hero,
                                    text="0",
                                    foreground=cfg.THEME_ACCENT,
                                    background=cfg.THEME_SURFACE,
                                    font=(cfg.FONT_BODY[0], 36, "bold"))
        self._lbl_total.grid(row=0, column=0, pady=(16, 2))
        ttk.Label(hero, text="Teile gescannt (gesamt)",
                  style="Surface.TLabel",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=1, column=0, pady=(0, 16))

        # Behälter-Balken
        ttk.Label(frm, text="Teile je Behälter",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        bar_frm = ttk.Frame(frm, style="Surface.TFrame")
        bar_frm.grid(row=2, column=0, padx=16, pady=4, sticky="ew")
        bar_frm.columnconfigure(1, weight=1)

        self._stat_bars   = {}
        self._stat_labels = {}
        for i in range(1, 7):
            ttk.Label(bar_frm, text=f"Behälter {i}:",
                      style="Surface.Muted.TLabel").grid(
                row=i - 1, column=0, padx=(10, 8), pady=5, sticky="w")
            bar_var = tk.IntVar(value=0)
            bar = ttk.Progressbar(bar_frm, variable=bar_var,
                                  maximum=100, length=200)
            bar.grid(row=i - 1, column=1, padx=4, pady=5, sticky="ew")
            lbl = ttk.Label(bar_frm, text="0",
                            style="Surface.TLabel", width=6, anchor="e")
            lbl.grid(row=i - 1, column=2, padx=(4, 10))
            self._stat_bars[i]   = bar_var
            self._stat_labels[i] = lbl

    # ------------------------------------------------------------------
    # Tab: Auftragsfortschritt
    # ------------------------------------------------------------------

    def _build_progress(self):
        frm = self._tab_progress
        frm.columnconfigure(0, weight=1)

        sel_frm = ttk.Frame(frm)
        sel_frm.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        sel_frm.columnconfigure(1, weight=1)

        ttk.Label(sel_frm, text="Auftrag:").grid(
            row=0, column=0, padx=(0, 8), sticky="w")
        self._prog_order_var = tk.StringVar()
        self._prog_combo = ttk.Combobox(sel_frm,
                                         textvariable=self._prog_order_var,
                                         state="readonly")
        self._prog_combo.grid(row=0, column=1, sticky="ew")
        self._prog_combo.bind("<<ComboboxSelected>>",
                              self._refresh_progress)

        prog_frm = ttk.Frame(frm, style="Surface.TFrame")
        prog_frm.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        prog_frm.columnconfigure(2, weight=1)

        self._prog_bars = {}
        self._prog_lbls = {}
        for i in range(1, 7):
            ttk.Label(prog_frm, text=f"Behälter {i}:",
                      style="Surface.Muted.TLabel").grid(
                row=i - 1, column=0, padx=(10, 8), pady=6, sticky="w")
            bar_var = tk.IntVar(value=0)
            bar = ttk.Progressbar(prog_frm, variable=bar_var,
                                  maximum=100, length=220)
            bar.grid(row=i - 1, column=1, padx=4, pady=6, sticky="ew")
            lbl = ttk.Label(prog_frm, text="0 / 0",
                            style="Surface.TLabel", width=10, anchor="e")
            lbl.grid(row=i - 1, column=2, padx=(4, 10))
            self._prog_bars[i] = bar_var
            self._prog_lbls[i] = lbl

    # ------------------------------------------------------------------
    # Tab: Inventar
    # ------------------------------------------------------------------

    def _build_inventory(self):
        frm = self._tab_inventory
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(0, weight=1)

        tree_frm = ttk.Frame(frm)
        tree_frm.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        tree_frm.columnconfigure(0, weight=1)
        tree_frm.rowconfigure(0, weight=1)

        cols = ("part_num", "name", "color_name", "container", "count", "updated_at")
        self._inv_tree = ttk.Treeview(tree_frm, columns=cols,
                                       show="headings", height=12)
        heads = {
            "part_num":   ("Teilenummer", 120),
            "name":       ("Name",        180),
            "color_name": ("Farbe",       130),
            "container":  ("Behälter",     70),
            "count":      ("Anzahl",        70),
            "updated_at": ("Aktualisiert", 130),
        }
        for col, (text, width) in heads.items():
            self._inv_tree.heading(col, text=text)
            self._inv_tree.column(col, width=width,
                                   anchor="center" if col in
                                   ("container", "count") else "w")
        self._inv_tree.grid(row=0, column=0, sticky="nsew")

        sb_v = ttk.Scrollbar(tree_frm, orient="vertical",
                             command=self._inv_tree.yview)
        sb_v.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(tree_frm, orient="horizontal",
                             command=self._inv_tree.xview)
        sb_h.grid(row=1, column=0, sticky="ew")
        self._inv_tree.configure(yscrollcommand=sb_v.set,
                                  xscrollcommand=sb_h.set)

    # ------------------------------------------------------------------
    # Tab: Scan-Log
    # ------------------------------------------------------------------

    def _build_log(self):
        frm = self._tab_log
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(0, weight=1)

        tree_frm = ttk.Frame(frm)
        tree_frm.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        tree_frm.columnconfigure(0, weight=1)
        tree_frm.rowconfigure(0, weight=1)

        cols = ("scanned_at", "part_num", "name", "color_name", "score", "container")
        self._log_tree = ttk.Treeview(tree_frm, columns=cols,
                                       show="headings", height=14)
        heads = {
            "scanned_at": ("Zeitstempel",  140),
            "part_num":   ("Teilenummer",  110),
            "name":       ("Name",         160),
            "color_name": ("Farbe",        120),
            "score":      ("Konfidenz",     80),
            "container":  ("Behälter",      70),
        }
        for col, (text, width) in heads.items():
            self._log_tree.heading(col, text=text)
            self._log_tree.column(col, width=width,
                                   anchor="center" if col in
                                   ("score", "container") else "w")
        self._log_tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frm, orient="vertical",
                           command=self._log_tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._log_tree.configure(yscrollcommand=sb.set)

    # ------------------------------------------------------------------
    # Aktualisierungen
    # ------------------------------------------------------------------

    def on_show(self):
        threading.Thread(target=self._load_data_bg, daemon=True).start()

    # ------------------------------------------------------------------
    # Hintergrund-Laden aller Daten
    # ------------------------------------------------------------------

    def _load_data_bg(self):
        """Lädt alle Daten außerhalb des UI-Threads und übergibt sie dann."""
        db = self.app.db
        if not db:
            return
        try:
            stats     = db.get_scan_stats()
            orders    = db.get_orders()
            inventory = db.get_inventory()
            log       = db.get_scan_log(limit=200)
            progress  = db.get_order_progress(orders[0]["id"]) if orders else {}
        except Exception:
            return
        self.after(0, lambda: self._apply_data(stats, orders, inventory,
                                               log, progress))

    def _apply_data(self, stats, orders, inventory, log, progress):
        """Aktualisiert alle Widgets im UI-Thread mit den vorab geladenen Daten."""
        self._apply_stats(stats)
        self._apply_orders_combo(orders, progress)
        self._apply_inventory(inventory)
        self._apply_log(log)

    # ------------------------------------------------------------------
    # Einzelne Apply-Methoden (laufen im UI-Thread)
    # ------------------------------------------------------------------

    def _apply_stats(self, stats):
        self._lbl_total.configure(text=str(stats["total"]))
        per_c = stats["per_container"]
        max_val = max(per_c.values(), default=1)
        for i in range(1, 7):
            cnt = per_c.get(i, 0)
            pct = int(100 * cnt / max_val) if max_val else 0
            self._stat_bars[i].set(pct)
            self._stat_labels[i].configure(text=str(cnt))

    def _apply_orders_combo(self, orders, progress):
        self._orders_cache = orders
        names = [o["name"] for o in orders]
        self._prog_combo["values"] = names
        if names:
            self._prog_combo.current(0)
            self._apply_progress(progress)

    def _apply_progress(self, progress):
        for i in range(1, 7):
            d = progress.get(i, {"required": 0, "fulfilled": 0, "percent": 0})
            self._prog_bars[i].set(d["percent"])
            self._prog_lbls[i].configure(
                text=f"{d['fulfilled']} / {d['required']}")

    def _apply_inventory(self, inventory):
        # Alle Zeilen in einem einzigen Tcl-Aufruf löschen statt einer Schleife
        self._inv_tree.delete(*self._inv_tree.get_children())
        for item in inventory:
            self._inv_tree.insert("", "end", values=(
                item["part_num"],
                item["name"],
                item.get("color_name", ""),
                item["container"],
                item["count"],
                item["updated_at"][:16],
            ))

    def _apply_log(self, log):
        self._log_tree.delete(*self._log_tree.get_children())
        for entry in log:
            self._log_tree.insert("", "end", values=(
                entry["scanned_at"][:16],
                entry["part_num"],
                entry["name"],
                entry.get("color_name", ""),
                f"{entry['score']:.0%}",
                entry["container"],
            ))

    # ------------------------------------------------------------------
    # Ältere Refresh-Methoden – delegieren an den Hintergrund-Lader
    # ------------------------------------------------------------------

    def _refresh_stats(self):
        db = self.app.db
        if not db:
            return

        def _load():
            try:
                stats = db.get_scan_stats()
            except Exception:
                return
            self.after(0, lambda s=stats: self._apply_stats(s))

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_orders_combo(self):
        db = self.app.db
        if not db:
            return

        def _load():
            try:
                orders = db.get_orders()
                progress = db.get_order_progress(orders[0]["id"]) if orders else {}
            except Exception:
                return
            self.after(0, lambda o=orders, p=progress:
                       self._apply_orders_combo(o, p))

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_progress(self, _event=None):
        db = self.app.db
        if not db or not hasattr(self, "_orders_cache"):
            return
        sel = self._prog_order_var.get()
        order_id = None
        for o in self._orders_cache:
            if o["name"] == sel:
                order_id = o["id"]
                break
        if order_id is None:
            return

        def _load():
            try:
                progress = db.get_order_progress(order_id)
            except Exception:
                return
            self.after(0, lambda p=progress: self._apply_progress(p))

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_inventory(self):
        db = self.app.db
        if not db:
            return

        def _load():
            try:
                inventory = db.get_inventory()
            except Exception:
                return
            self.after(0, lambda inv=inventory: self._apply_inventory(inv))

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_log(self):
        db = self.app.db
        if not db:
            return

        def _load():
            try:
                log = db.get_scan_log(limit=200)
            except Exception:
                return
            self.after(0, lambda l=log: self._apply_log(l))

        threading.Thread(target=_load, daemon=True).start()

    def _reset_inventory(self):
        if messagebox.askyesno(
                "Inventar zurücksetzen",
                "Alle Inventar-Daten werden gelöscht!\nFortfahren?",
                parent=self):
            self.app.db.reset_inventory()
            self._refresh_inventory()
            self._refresh_stats()
