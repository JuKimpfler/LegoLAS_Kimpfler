"""
SQLite-Datenbank für LegoLAS.

Tabellen:
  - inventory   : Gezählte Teile mit Teilenummer, Farbe, Name, Anzahl und Behälter.
  - scan_log    : Jeder einzelne Scan mit Zeitstempel, Ergebnis, Konfidenz.
  - settings    : Allgemeine Schlüssel-Wert-Einstellungen (JSON-Blob).
  - servo_cal   : Kalibrierte Servo-Positionen pro Behälter-Slot.
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """
    Datenbankschicht für LegoLAS.

    Parameter
    ---------
    db_path : str
        Pfad zur SQLite-Datei.
    config : module
        Konfigurationsmodul (für DEFAULT_SERVO_POSITIONS).
    """

    def __init__(self, db_path: str, config):
        self.db_path = db_path
        self.cfg = config
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()   # Serialisiert alle DB-Zugriffe über Threads
        self._connect()
        self._create_tables()
        self._migrate_schema()

    # ------------------------------------------------------------------
    # Verbindung
    # ------------------------------------------------------------------

    def _connect(self):
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_tables(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS inventory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                part_num    TEXT    NOT NULL,
                name        TEXT    NOT NULL DEFAULT '',
                color_name  TEXT    NOT NULL DEFAULT '',
                container   INTEGER NOT NULL DEFAULT 6,
                count       INTEGER NOT NULL DEFAULT 0,
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(part_num, color_name, container)
            );

            CREATE TABLE IF NOT EXISTS scan_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                part_num    TEXT    NOT NULL,
                name        TEXT    NOT NULL DEFAULT '',
                color_name  TEXT    NOT NULL DEFAULT '',
                score       REAL    NOT NULL DEFAULT 0.0,
                container   INTEGER NOT NULL DEFAULT 6,
                order_id    INTEGER
            );

            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                completed   INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                part_num    TEXT    NOT NULL,
                color_name  TEXT    NOT NULL DEFAULT '',
                container   INTEGER NOT NULL,
                required    INTEGER NOT NULL DEFAULT 0,
                fulfilled   INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS servo_cal (
                slot        INTEGER PRIMARY KEY,
                angle       REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL
            );
        """)
        self._conn.commit()
        self._init_servo_cal()

    def _migrate_schema(self):
        """Ergänzt fehlende Spalten in bestehenden Datenbanken."""
        cur = self._conn.cursor()

        # -- inventory: color_name + UNIQUE(part_num, color_name, container) --
        cur.execute("PRAGMA table_info(inventory)")
        inv_cols = {row["name"] for row in cur.fetchall()}
        if "color_name" not in inv_cols:
            self._conn.executescript("""
                CREATE TABLE inventory_new (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_num    TEXT    NOT NULL,
                    name        TEXT    NOT NULL DEFAULT '',
                    color_name  TEXT    NOT NULL DEFAULT '',
                    container   INTEGER NOT NULL DEFAULT 6,
                    count       INTEGER NOT NULL DEFAULT 0,
                    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                    UNIQUE(part_num, color_name, container)
                );
                INSERT INTO inventory_new
                    (part_num, name, color_name, container, count, updated_at)
                SELECT part_num, name, '', container, count, updated_at
                FROM inventory;
                DROP TABLE inventory;
                ALTER TABLE inventory_new RENAME TO inventory;
            """)

        # -- scan_log: color_name --
        cur.execute("PRAGMA table_info(scan_log)")
        sl_cols = {row["name"] for row in cur.fetchall()}
        if "color_name" not in sl_cols:
            self._conn.execute(
                "ALTER TABLE scan_log ADD COLUMN color_name TEXT NOT NULL DEFAULT ''")
            self._conn.commit()

        # -- order_items: color_name --
        cur.execute("PRAGMA table_info(order_items)")
        oi_cols = {row["name"] for row in cur.fetchall()}
        if "color_name" not in oi_cols:
            self._conn.execute(
                "ALTER TABLE order_items ADD COLUMN color_name TEXT NOT NULL DEFAULT ''")
            self._conn.commit()

    def _init_servo_cal(self):
        """Füllt Servo-Kalibriertabelle mit Standardwerten, falls leer."""
        cur = self._conn.cursor()
        for slot, angle in self.cfg.DEFAULT_SERVO_POSITIONS.items():
            cur.execute(
                "INSERT OR IGNORE INTO servo_cal (slot, angle) VALUES (?,?)",
                (slot, angle),
            )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Inventar
    # ------------------------------------------------------------------

    def add_part(self, part_num: str, name: str,
                 container: int, count: int = 1, color_name: str = ""):
        """Erhöht den Bestand eines Teils im angegebenen Behälter."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                INSERT INTO inventory (part_num, name, color_name, container, count, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(part_num, color_name, container) DO UPDATE SET
                    count      = count + excluded.count,
                    name       = excluded.name,
                    updated_at = datetime('now')
            """, (part_num, name, color_name, container, count))
            self._conn.commit()

    def get_inventory(self) -> List[dict]:
        """Gibt alle Inventareinträge zurück."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT part_num, name, color_name, container, count, updated_at
                FROM inventory ORDER BY container, part_num
            """)
            return [dict(row) for row in cur.fetchall()]

    def get_part_total(self, part_num: str) -> int:
        """Gesamtanzahl aller Einträge für eine Teilenummer."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT COALESCE(SUM(count),0) FROM inventory WHERE part_num=?",
                (part_num,),
            )
            return cur.fetchone()[0]

    def reset_inventory(self):
        """Löscht alle Inventareinträge."""
        with self._lock:
            self._conn.execute("DELETE FROM inventory")
            self._conn.commit()

    # ------------------------------------------------------------------
    # Scan-Log
    # ------------------------------------------------------------------

    def log_scan(self, part_num: str, name: str, score: float,
                 container: int, order_id: int = None, color_name: str = ""):
        with self._lock:
            self._conn.execute("""
                INSERT INTO scan_log (part_num, name, color_name, score, container, order_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (part_num, name, color_name, score, container, order_id))
            self._conn.commit()

    def get_scan_log(self, limit: int = 200) -> List[dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT * FROM scan_log ORDER BY scanned_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    def get_scan_stats(self) -> dict:
        """Gibt Statistiken zurück: Scans gesamt, Teile je Behälter."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM scan_log")
            total = cur.fetchone()["total"]
            cur.execute("""
                SELECT container, COUNT(*) AS cnt FROM scan_log
                GROUP BY container ORDER BY container
            """)
            per_container = {row["container"]: row["cnt"]
                             for row in cur.fetchall()}
        return {"total": total, "per_container": per_container}

    # ------------------------------------------------------------------
    # Servo-Kalibrierung
    # ------------------------------------------------------------------

    def get_servo_positions(self) -> Dict[int, float]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT slot, angle FROM servo_cal ORDER BY slot")
            return {row["slot"]: row["angle"] for row in cur.fetchall()}

    def set_servo_position(self, slot: int, angle: float):
        with self._lock:
            self._conn.execute("""
                INSERT INTO servo_cal (slot, angle) VALUES (?,?)
                ON CONFLICT(slot) DO UPDATE SET angle = excluded.angle
            """, (slot, angle))
            self._conn.commit()

    # ------------------------------------------------------------------
    # Einstellungen
    # ------------------------------------------------------------------

    def get_setting(self, key: str, default=None):
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cur.fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (ValueError, TypeError):
            return row["value"]

    def set_setting(self, key: str, value):
        with self._lock:
            self._conn.execute("""
                INSERT INTO settings (key, value) VALUES (?,?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, json.dumps(value)))
            self._conn.commit()

    # ------------------------------------------------------------------
    # Auftragsmanagement
    # ------------------------------------------------------------------

    def create_order(self, name: str,
                     items: List[Tuple[str, str, int, int]]) -> int:
        """
        Erstellt einen neuen Auftrag.

        Parameters
        ----------
        name : str
            Auftragsname.
        items : List[Tuple[part_num, color_name, container, required]]

        Returns
        -------
        Neue Auftrags-ID.
        """
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO orders (name) VALUES (?)", (name,))
            order_id = cur.lastrowid
            for part_num, color_name, container, required in items:
                cur.execute("""
                    INSERT INTO order_items (order_id, part_num, color_name, container, required)
                    VALUES (?,?,?,?,?)
                """, (order_id, part_num, color_name, container, required))
            self._conn.commit()
        return order_id

    def get_orders(self) -> List[dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM orders ORDER BY id DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_order_items(self, order_id: int) -> List[dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT * FROM order_items WHERE order_id=?
                ORDER BY container, part_num
            """, (order_id,))
            return [dict(row) for row in cur.fetchall()]

    def fulfill_order_item(self, order_id: int, part_num: str,
                           container: int, amount: int = 1):
        """Erhöht fulfilled-Zähler für ein Auftragsitem."""
        with self._lock:
            self._conn.execute("""
                UPDATE order_items
                SET fulfilled = MIN(fulfilled + ?, required)
                WHERE order_id=? AND part_num=? AND container=?
            """, (amount, order_id, part_num, container))
            self._conn.commit()
        self._check_order_completion(order_id)

    def _check_order_completion(self, order_id: int):
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT COUNT(*) AS remaining
                FROM order_items
                WHERE order_id=? AND fulfilled < required
            """, (order_id,))
            remaining = cur.fetchone()["remaining"]
            if remaining == 0:
                self._conn.execute(
                    "UPDATE orders SET completed=1 WHERE id=?", (order_id,))
                self._conn.commit()

    def get_order_progress(self, order_id: int) -> Dict[int, dict]:
        """
        Gibt Fortschritt je Behälter zurück.
        ``{container: {required, fulfilled, percent}}``
        """
        items = self.get_order_items(order_id)
        result: Dict[int, dict] = {}
        for item in items:
            c = item["container"]
            if c not in result:
                result[c] = {"required": 0, "fulfilled": 0}
            result[c]["required"] += item["required"]
            result[c]["fulfilled"] += item["fulfilled"]
        for c, d in result.items():
            req = d["required"]
            d["percent"] = round(100 * d["fulfilled"] / req) if req else 100
        return result

    def delete_order(self, order_id: int):
        with self._lock:
            self._conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
            self._conn.commit()

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def export_inventory_dict(self) -> List[dict]:
        return self.get_inventory()

    def import_inventory_dict(self, rows: List[dict]):
        """Importiert Inventar (überschreibt vorhandene Einträge)."""
        for row in rows:
            self.add_part(
                part_num=row.get("part_num", ""),
                name=row.get("name", ""),
                color_name=row.get("color_name", ""),
                container=int(row.get("container", 6)),
                count=int(row.get("count", 0)),
            )
