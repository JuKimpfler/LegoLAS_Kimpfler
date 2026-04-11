"""
Einstellungsansicht für LegoLAS GUI.

Einstellungen:
  - Bandgeschwindigkeit (Slider 0–100%)
  - Erkennungsschwelle / Konfidenz-Threshold (Slider 0–100%)
  - Kamera-Quelle (Geräte-Index oder DroidCam-URL)
  - Auftragslistenimport (Excel hochladen)
  - Exportoptionen (Auftrag, fehlende Teile, Inventar)
  - Behälter-Beschriftungen
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from .base import BaseView
from core.rebrickable import fetch_set_parts


class SettingsView(BaseView):

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="🛠  Einstellungen",
                  style="Title.TLabel").grid(
            row=0, column=0, pady=(16, 4), sticky="n")

        # Notebook mit Unter-Tabs
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        self._tab_general = ttk.Frame(nb)
        self._tab_orders  = ttk.Frame(nb)
        self._tab_export  = ttk.Frame(nb)
        nb.add(self._tab_general, text="  Allgemein  ")
        nb.add(self._tab_orders,  text="  Auftragslisten  ")
        nb.add(self._tab_export,  text="  Export  ")

        self._build_general()
        self._build_orders()
        self._build_export()

    # ------------------------------------------------------------------
    # Tab: Allgemein
    # ------------------------------------------------------------------

    def _build_general(self):
        frm = self._tab_general
        frm.columnconfigure(1, weight=1)

        row = 0

        # Bandgeschwindigkeit
        ttk.Label(frm, text="Bandgeschwindigkeit:").grid(
            row=row, column=0, padx=16, pady=14, sticky="w")
        self._speed_var = tk.IntVar(value=cfg.DEFAULT_BELT_SPEED)
        frm_sp = ttk.Frame(frm)
        frm_sp.grid(row=row, column=1, sticky="ew", padx=16)
        frm_sp.columnconfigure(0, weight=1)
        ttk.Scale(frm_sp, from_=10, to=100, orient="horizontal",
                  variable=self._speed_var,
                  command=self._on_speed_change).grid(
            row=0, column=0, sticky="ew")
        self._lbl_speed = ttk.Label(frm_sp,
                                    text=f"{cfg.DEFAULT_BELT_SPEED}%",
                                    width=5, anchor="e")
        self._lbl_speed.grid(row=0, column=1, padx=8)
        row += 1

        # Erkennungsschwelle
        ttk.Label(frm, text="Erkennungsschwelle:").grid(
            row=row, column=0, padx=16, pady=14, sticky="w")
        default_thresh = int(cfg.DEFAULT_CONF_THRESHOLD * 100)
        self._thresh_var = tk.IntVar(value=default_thresh)
        frm_th = ttk.Frame(frm)
        frm_th.grid(row=row, column=1, sticky="ew", padx=16)
        frm_th.columnconfigure(0, weight=1)
        ttk.Scale(frm_th, from_=10, to=100, orient="horizontal",
                  variable=self._thresh_var,
                  command=self._on_thresh_change).grid(
            row=0, column=0, sticky="ew")
        self._lbl_thresh = ttk.Label(frm_th, text=f"{default_thresh}%",
                                     width=5, anchor="e")
        self._lbl_thresh.grid(row=0, column=1, padx=8)
        row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=8)
        row += 1

        # DroidCam URL
        ttk.Label(frm, text="DroidCam URL\n(lokale IP):").grid(
            row=row, column=0, padx=16, pady=10, sticky="w")
        self._droidcam_url_var = tk.StringVar(value=cfg.DROIDCAM_URL)
        ttk.Entry(frm, textvariable=self._droidcam_url_var, width=36).grid(
            row=row, column=1, padx=16, sticky="ew")
        row += 1

        # Rebrickable API Key
        ttk.Label(frm, text="Rebrickable API Key:").grid(
            row=row, column=0, padx=16, pady=10, sticky="w")
        self._rebrickable_key_var = tk.StringVar(value=cfg.REBRICKABLE_API_KEY)
        ttk.Entry(frm, textvariable=self._rebrickable_key_var, width=36).grid(
            row=row, column=1, padx=16, sticky="ew")
        row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=8)
        row += 1

        # Behälter-Beschriftungen
        ttk.Label(frm, text="Behälter-Namen:").grid(
            row=row, column=0, padx=16, pady=(8, 4), sticky="nw")
        label_frm = ttk.Frame(frm)
        label_frm.grid(row=row, column=1, padx=16, pady=(8, 4), sticky="ew")
        label_frm.columnconfigure(1, weight=1)
        self._container_labels = {}
        for i in range(1, 7):
            ttk.Label(label_frm, text=f"Behälter {i}:").grid(
                row=i - 1, column=0, padx=(0, 8), pady=3, sticky="w")
            var = tk.StringVar(value=f"Behälter {i}")
            ttk.Entry(label_frm, textvariable=var, width=22).grid(
                row=i - 1, column=1, pady=3, sticky="ew")
            self._container_labels[i] = var
        row += 1

        ttk.Button(frm, text="💾  Einstellungen speichern",
                   command=self._save_settings,
                   style="Accent.TButton").grid(
            row=row, column=0, columnspan=2, pady=16)

    # ------------------------------------------------------------------
    # Tab: Auftragslisten
    # ------------------------------------------------------------------

    def _build_orders(self):
        frm = self._tab_orders
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(8, weight=1)

        # --- Excel Import ---
        ttk.Label(frm,
                  text="Excel-Auftragsliste importieren\n"
                       "(Spalten: Teilenummer | Name | Anzahl | Behälter)",
                  justify="left").grid(
            row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        ttk.Button(frm, text="📂  Excel importieren",
                   command=self._import_order,
                   style="Accent.TButton").grid(
            row=1, column=0, padx=16, pady=8, sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(
            row=2, column=0, sticky="ew", padx=16, pady=8)

        # --- Rebrickable Set Import ---
        ttk.Label(frm,
                  text="🌐  Auftrag aus LEGO-Set importieren (Rebrickable)",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=3, column=0, padx=16, pady=(8, 4), sticky="w")

        rb_frm = ttk.Frame(frm)
        rb_frm.grid(row=4, column=0, padx=16, pady=4, sticky="ew")
        rb_frm.columnconfigure(1, weight=1)

        ttk.Label(rb_frm, text="Set-ID (z. B. 75192-1):").grid(
            row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        self._rb_set_id_var = tk.StringVar()
        ttk.Entry(rb_frm, textvariable=self._rb_set_id_var, width=20).grid(
            row=0, column=1, pady=4, sticky="w")

        ttk.Label(rb_frm, text="Ziel-Behälter:").grid(
            row=1, column=0, padx=(0, 8), pady=4, sticky="w")
        self._rb_container_var = tk.StringVar(value="1")
        ttk.Combobox(rb_frm,
                     textvariable=self._rb_container_var,
                     values=["1", "2", "3", "4", "5", "6"],
                     width=6,
                     state="readonly").grid(
            row=1, column=1, pady=4, sticky="w")

        btn_frm = ttk.Frame(frm)
        btn_frm.grid(row=5, column=0, padx=16, pady=(4, 8), sticky="w")
        self._rb_import_btn = ttk.Button(
            btn_frm,
            text="🔄  Set importieren",
            command=self._import_from_rebrickable,
            style="Accent.TButton")
        self._rb_import_btn.pack(side="left")
        self._rb_status_lbl = ttk.Label(btn_frm, text="", style="Muted.TLabel")
        self._rb_status_lbl.pack(side="left", padx=10)

        ttk.Separator(frm, orient="horizontal").grid(
            row=6, column=0, sticky="ew", padx=16, pady=8)

        ttk.Label(frm, text="Vorhandene Aufträge:").grid(
            row=7, column=0, padx=16, pady=(8, 4), sticky="w")

        # Tabelle
        tree_frm = ttk.Frame(frm)
        tree_frm.grid(row=8, column=0, padx=16, pady=4, sticky="nsew")
        tree_frm.columnconfigure(0, weight=1)
        tree_frm.rowconfigure(0, weight=1)

        self._orders_tree = ttk.Treeview(tree_frm,
                                          columns=("id", "name", "created",
                                                   "done"),
                                          show="headings", height=8)
        self._orders_tree.heading("id",      text="ID")
        self._orders_tree.heading("name",    text="Name")
        self._orders_tree.heading("created", text="Erstellt")
        self._orders_tree.heading("done",    text="Abgeschlossen")
        self._orders_tree.column("id",      width=40,  anchor="center")
        self._orders_tree.column("name",    width=180)
        self._orders_tree.column("created", width=130)
        self._orders_tree.column("done",    width=80,  anchor="center")
        self._orders_tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frm, orient="vertical",
                           command=self._orders_tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._orders_tree.configure(yscrollcommand=sb.set)

        ttk.Button(frm, text="🗑  Ausgewählten Auftrag löschen",
                   command=self._delete_order,
                   style="Danger.TButton").grid(
            row=9, column=0, padx=16, pady=8, sticky="w")

    # ------------------------------------------------------------------
    # Tab: Export
    # ------------------------------------------------------------------

    def _build_export(self):
        frm = self._tab_export
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="Exportoptionen",
                  font=(cfg.FONT_BODY[0], cfg.FONT_BODY[1], "bold")).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        exports = [
            ("📊  Inventar als Excel exportieren",    self._export_inventory),
            ("📋  Auftrag als Excel exportieren",      self._export_order),
            ("❓  Fehlende Teile exportieren",          self._export_missing),
            ("💾  Datenbank exportieren (DB-Datei)",   self._export_db),
            ("📥  Datenbank importieren (DB-Datei)",   self._import_db),
        ]
        for i, (label, cmd) in enumerate(exports):
            ttk.Button(frm, text=label, command=cmd,
                       style="TButton").grid(
                row=i + 1, column=0, padx=16, pady=6, sticky="ew")

    # ------------------------------------------------------------------
    # Event-Handler: Allgemein
    # ------------------------------------------------------------------

    def _on_speed_change(self, _=None):
        val = self._speed_var.get()
        self._lbl_speed.configure(text=f"{val}%")
        engine = self.app.engine
        if engine:
            engine.belt_speed = val

    def _on_thresh_change(self, _=None):
        val = self._thresh_var.get()
        self._lbl_thresh.configure(text=f"{val}%")
        engine = self.app.engine
        if engine:
            engine.conf_threshold = val / 100.0

    def _save_settings(self):
        db = self.app.db
        if not db:
            return
        db.set_setting("belt_speed", self._speed_var.get())
        db.set_setting("conf_threshold", self._thresh_var.get() / 100.0)
        db.set_setting("droidcam_url", self._droidcam_url_var.get())
        db.set_setting("rebrickable_api_key", self._rebrickable_key_var.get())
        labels = {str(k): v.get() for k, v in self._container_labels.items()}
        db.set_setting("container_labels", labels)
        messagebox.showinfo("Gespeichert",
                            "Einstellungen wurden gespeichert.",
                            parent=self)

    # ------------------------------------------------------------------
    # Event-Handler: Aufträge
    # ------------------------------------------------------------------

    def _import_order(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Auftragsliste öffnen",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Alle", "*.*")],
        )
        if not path:
            return
        om = self.app.order_manager
        db = self.app.db
        if not om or not db:
            return

        def _run():
            try:
                name, items = om.import_order(path)
                order_id = db.create_order(name, items)
                self.after(0, lambda: _done(name, len(items), order_id))
            except Exception as exc:
                self.after(0, lambda msg=str(exc):
                           messagebox.showerror("Fehler", msg, parent=self))

        def _done(name, count, order_id):
            messagebox.showinfo(
                "Importiert",
                f"Auftrag '{name}' mit {count} Positionen importiert "
                f"(ID={order_id}).",
                parent=self,
            )
            self._refresh_orders()

        threading.Thread(target=_run, daemon=True).start()

    def _import_from_rebrickable(self):
        set_id = self._rb_set_id_var.get().strip()
        if not set_id:
            messagebox.showerror("Fehler",
                                 "Bitte eine Set-ID eingeben (z. B. 75192-1).",
                                 parent=self)
            return

        try:
            container = int(self._rb_container_var.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiger Behälter.", parent=self)
            return

        db = self.app.db
        if not db:
            return

        api_key = db.get_setting("rebrickable_api_key", "")
        if not api_key:
            messagebox.showerror(
                "Fehlender API Key",
                "Kein Rebrickable API Key konfiguriert.\n"
                "Bitte den Key im Tab 'Allgemein' eintragen und speichern.",
                parent=self)
            return

        self._rb_import_btn.configure(state="disabled")
        self._rb_status_lbl.configure(text="⏳ Lade Daten von Rebrickable…")
        self.update_idletasks()

        def _run():
            try:
                parts = fetch_set_parts(set_id, api_key)
                order_name = f"Set {set_id if set_id.endswith('-1') else set_id + '-1'}"
                items = [
                    (part_num, color_name, container, qty)
                    for part_num, _name, color_name, qty in parts
                ]
                self.after(0, lambda: _done(order_name, items))
            except Exception as exc:
                self.after(0, lambda msg=str(exc): _error(msg))

        def _done(name, items):
            try:
                order_id = db.create_order(name, items)
                self._rb_status_lbl.configure(
                    text=f"✅ {len(items)} Teile importiert")
                messagebox.showinfo(
                    "Importiert",
                    f"Auftrag '{name}' mit {len(items)} Teilen importiert "
                    f"(ID={order_id}).",
                    parent=self)
                self._refresh_orders()
            except Exception as exc:
                messagebox.showerror("Fehler", str(exc), parent=self)
                self._rb_status_lbl.configure(text="❌ Fehler")
            finally:
                self._rb_import_btn.configure(state="normal")

        def _error(msg):
            messagebox.showerror("Fehler beim Laden", msg, parent=self)
            self._rb_status_lbl.configure(text="❌ Fehler")
            self._rb_import_btn.configure(state="normal")

        threading.Thread(target=_run, daemon=True).start()

    def _delete_order(self):
        sel = self._orders_tree.selection()
        if not sel:
            return
        order_id = int(self._orders_tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Löschen",
                               f"Auftrag {order_id} wirklich löschen?",
                               parent=self):
            self.app.db.delete_order(order_id)
            self._refresh_orders()

    def _refresh_orders(self):
        for row in self._orders_tree.get_children():
            self._orders_tree.delete(row)
        db = self.app.db
        if not db:
            return
        for order in db.get_orders():
            self._orders_tree.insert("", "end", values=(
                order["id"],
                order["name"],
                order["created_at"][:16],
                "✅" if order["completed"] else "",
            ))

    # ------------------------------------------------------------------
    # Event-Handler: Export
    # ------------------------------------------------------------------

    def _export_inventory(self):
        self._run_export("inventar.xlsx",
                         lambda path: self.app.order_manager.export_inventory(
                             self.app.db.get_inventory(), path))

    def _export_order(self):
        db = self.app.db
        om = self.app.order_manager
        if not db or not om:
            return
        orders = db.get_orders()
        if not orders:
            messagebox.showinfo("Hinweis", "Keine Aufträge vorhanden.",
                                parent=self)
            return
        order = orders[0]
        items = db.get_order_items(order["id"])
        self._run_export(f"{order['name']}_auftrag.xlsx",
                         lambda path: om.export_order(
                             order["name"], items, path))

    def _export_missing(self):
        db = self.app.db
        om = self.app.order_manager
        if not db or not om:
            return
        orders = db.get_orders()
        if not orders:
            messagebox.showinfo("Hinweis", "Keine Aufträge vorhanden.",
                                parent=self)
            return
        order = orders[0]
        items = db.get_order_items(order["id"])
        self._run_export(f"{order['name']}_fehlend.xlsx",
                         lambda path: om.export_missing_parts(
                             order["name"], items, path))

    def _export_db(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Datenbank speichern",
            defaultextension=".db",
            filetypes=[("SQLite", "*.db"), ("Alle", "*.*")],
        )
        if not path:
            return
        import shutil
        shutil.copy2(self.app.db.db_path, path)
        messagebox.showinfo("Exportiert", f"Datenbank gespeichert:\n{path}",
                            parent=self)

    def _import_db(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Datenbank importieren",
            filetypes=[("SQLite", "*.db"), ("Alle", "*.*")],
        )
        if not path:
            return
        if not messagebox.askyesno(
                "Achtung",
                "Aktuelle Datenbank wird ÜBERSCHRIEBEN!\nFortfahren?",
                parent=self):
            return
        import shutil
        self.app.db.close()
        shutil.copy2(path, self.app.db.db_path)
        self.app.db._connect()
        self.app.db._create_tables()
        messagebox.showinfo("Importiert",
                            "Datenbank wurde importiert.", parent=self)

    def _run_export(self, default_name: str, export_func):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportieren als",
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Alle", "*.*")],
        )
        if not path:
            return
        try:
            export_func(path)
            messagebox.showinfo("Exportiert",
                                f"Datei gespeichert:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc), parent=self)

    def on_show(self):
        self._refresh_orders()
        db = self.app.db
        if db:
            speed = db.get_setting("belt_speed", cfg.DEFAULT_BELT_SPEED)
            self._speed_var.set(int(speed))
            thresh = db.get_setting("conf_threshold",
                                    cfg.DEFAULT_CONF_THRESHOLD)
            self._thresh_var.set(int(thresh * 100))
            labels = db.get_setting("container_labels", {})
            for k, var in self._container_labels.items():
                var.set(labels.get(str(k), f"Behälter {k}"))
            rb_key = db.get_setting("rebrickable_api_key",
                                    cfg.REBRICKABLE_API_KEY)
            self._rebrickable_key_var.set(rb_key or "")
