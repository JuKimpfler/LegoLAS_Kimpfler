"""
LEGO SORTIERMASCHINE - SET-MODUS ERWEITERUNG
=============================================

Diese Datei erweitert das Hauptprogramm um Set-Sammel-Funktionalität.

INSTALLATION:
1. Diesen Code am Ende von lego_sorter_gui.py einfügen (vor def main())
2. In LegoSorterGUI.__init__() hinzufügen:
   self.set_manager = SetManager()
   self.set_mode_active = False
3. In init_ui() den Tab-Container erweitern (siehe unten)

VERWENDUNG:
- CSV-Format: Teil-ID,Anzahl,Behälter
- Optional erste Zeile: SET_NAME: Dein Set-Name
- Import über "Set-Verwaltung" Tab
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QProgressBar, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import csv
import json
from pathlib import Path
from threading import Lock
from collections import defaultdict


# ══════════════════════════════════════════════════════════════
#                    SET-MANAGER (Backend)
# ══════════════════════════════════════════════════════════════

class SetManager:
    """Verwaltet LEGO-Sets und deren Teile-Listen"""
    
    def __init__(self):
        self.sets = {}  # set_name: {parts: {part_id: {bin: count}}, collected: {part_id: {bin: count}}}
        self.active_sets = []  # Liste aktiver Set-Namen
        self.lock = Lock()
        self.sets_dir = Path.home() / ".lego_sorter" / "sets"
        self.sets_dir.mkdir(parents=True, exist_ok=True)
    
    def load_set_from_csv(self, csv_path: str, set_name: str = None) -> tuple[bool, str]:
        """
        Lädt Set-Liste aus CSV-Datei
        
        CSV-Format:
        Zeile 1 (Optional): SET_NAME: LEGO City 60215
        Zeile 2: Teil-ID,Anzahl,Behälter
        Zeile 3+: 3001,10,1
        
        Returns: (success, message)
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return False, "CSV-Datei ist leer"
            
            # Erste Zeile prüfen: Set-Name?
            first_line = lines[0].strip()
            start_line = 0
            
            if first_line.upper().startswith("SET_NAME:"):
                set_name = first_line.split(":", 1)[1].strip()
                start_line = 1
            elif set_name is None:
                # Set-Name aus Dateinamen generieren
                set_name = Path(csv_path).stem
            
            # CSV parsen
            parts_dict = {}  # {part_id: {bin_number: count}}
            
            reader = csv.DictReader(lines[start_line:])
            
            for row in reader:
                part_id = row.get("Teil-ID", "").strip()
                count = int(row.get("Anzahl", 0))
                bin_num = int(row.get("Behälter", 10))  # Standard: Behälter 10
                
                if not part_id or count <= 0:
                    continue
                
                if part_id not in parts_dict:
                    parts_dict[part_id] = {}
                
                parts_dict[part_id][bin_num] = parts_dict[part_id].get(bin_num, 0) + count
            
            if not parts_dict:
                return False, "Keine gültigen Teile in CSV gefunden"
            
            # Set speichern
            with self.lock:
                self.sets[set_name] = {
                    "parts": parts_dict,
                    "collected": {},  # {part_id: {bin: count}}
                    "overflow": 0,
                    "csv_path": csv_path
                }
            
            # Set-Datei lokal speichern
            self._save_set_to_file(set_name)
            
            total_parts = sum(sum(bins.values()) for bins in parts_dict.values())
            return True, f"Set '{set_name}' geladen: {len(parts_dict)} Teiltypen, {total_parts} Teile gesamt"
            
        except Exception as e:
            return False, f"Fehler beim Laden: {e}"
    
    def _save_set_to_file(self, set_name: str):
        """Set lokal speichern"""
        try:
            set_file = self.sets_dir / f"{set_name}.json"
            with open(set_file, 'w', encoding='utf-8') as f:
                json.dump(self.sets[set_name], f, indent=4)
        except Exception as e:
            print(f"Fehler beim Speichern von Set '{set_name}': {e}")
    
    def load_saved_sets(self) -> list:
        """Alle gespeicherten Sets laden"""
        loaded = []
        for set_file in self.sets_dir.glob("*.json"):
            try:
                with open(set_file, 'r', encoding='utf-8') as f:
                    set_data = json.load(f)
                    set_name = set_file.stem
                    with self.lock:
                        self.sets[set_name] = set_data
                    loaded.append(set_name)
            except Exception as e:
                print(f"Fehler beim Laden von {set_file}: {e}")
        return loaded
    
    def activate_set(self, set_name: str):
        """Set aktivieren"""
        with self.lock:
            if set_name in self.sets and set_name not in self.active_sets:
                self.active_sets.append(set_name)
                return True
        return False
    
    def deactivate_set(self, set_name: str):
        """Set deaktivieren"""
        with self.lock:
            if set_name in self.active_sets:
                self.active_sets.remove(set_name)
                return True
        return False
    
    def delete_set(self, set_name: str):
        """Set löschen"""
        with self.lock:
            if set_name in self.sets:
                del self.sets[set_name]
            if set_name in self.active_sets:
                self.active_sets.remove(set_name)
        
        # Datei löschen
        set_file = self.sets_dir / f"{set_name}.json"
        if set_file.exists():
            set_file.unlink()
    
    def reset_set(self, set_name: str):
        """Set-Fortschritt zurücksetzen"""
        with self.lock:
            if set_name in self.sets:
                self.sets[set_name]["collected"] = {}
                self.sets[set_name]["overflow"] = 0
                self._save_set_to_file(set_name)
                return True
        return False
    
    def add_collected_part(self, part_id: str, bin_number: int) -> tuple[str, bool]:
        """
        Teil als gesammelt markieren
        
        Returns: (set_name oder "overflow", is_complete)
        """
        with self.lock:
            # Prüfe alle aktiven Sets
            for set_name in self.active_sets:
                set_data = self.sets[set_name]
                parts = set_data["parts"]
                
                # Ist dieses Teil in diesem Set für diesen Behälter benötigt?
                if part_id in parts and bin_number in parts[part_id]:
                    needed = parts[part_id][bin_number]
                    
                    # Bereits gesammelt
                    if part_id not in set_data["collected"]:
                        set_data["collected"][part_id] = {}
                    
                    current = set_data["collected"][part_id].get(bin_number, 0)
                    
                    # Noch nicht genug?
                    if current < needed:
                        set_data["collected"][part_id][bin_number] = current + 1
                        self._save_set_to_file(set_name)
                        
                        # Prüfe ob Set komplett
                        is_complete = self.is_set_complete(set_name)
                        return set_name, is_complete
            
            # Teil gehört zu keinem aktiven Set oder Limit erreicht → Overflow
            for set_name in self.active_sets:
                self.sets[set_name]["overflow"] += 1
                self._save_set_to_file(set_name)
            
            return "overflow", False
    
    def get_bin_for_part(self, part_id: str, num_bins: int) -> int:
        """
        Bestimmt Behälter-Nummer für Teil basierend auf aktiven Sets
        
        Returns: Behälter-Nummer (1-num_bins)
        """
        with self.lock:
            for set_name in self.active_sets:
                set_data = self.sets[set_name]
                parts = set_data["parts"]
                
                if part_id in parts:
                    # Prüfe alle Behälter für dieses Teil
                    for bin_num, needed in parts[part_id].items():
                        current = set_data["collected"].get(part_id, {}).get(bin_num, 0)
                        
                        # Noch nicht genug in diesem Behälter?
                        if current < needed:
                            return bin_num
            
            # Teil gehört zu keinem Set oder alle voll → Letzter Behälter (Overflow)
            return num_bins
    
    def is_set_complete(self, set_name: str) -> bool:
        """Prüft ob Set komplett gesammelt ist"""
        with self.lock:
            if set_name not in self.sets:
                return False
            
            set_data = self.sets[set_name]
            parts = set_data["parts"]
            collected = set_data["collected"]
            
            for part_id, bins in parts.items():
                for bin_num, needed in bins.items():
                    current = collected.get(part_id, {}).get(bin_num, 0)
                    if current < needed:
                        return False
            
            return True
    
    def get_progress(self, set_name: str) -> dict:
        """Fortschritt für Set berechnen"""
        with self.lock:
            if set_name not in self.sets:
                return {}
            
            set_data = self.sets[set_name]
            parts = set_data["parts"]
            collected = set_data["collected"]
            
            # Gesamt-Fortschritt
            total_needed = sum(sum(bins.values()) for bins in parts.values())
            total_collected = sum(sum(bins.values()) for bins in collected.values())
            
            # Pro Behälter
            bin_progress = {}
            for bin_num in range(1, 11):  # Max 10 Behälter
                needed = 0
                current = 0
                
                for part_id, bins in parts.items():
                    if bin_num in bins:
                        needed += bins[bin_num]
                        current += collected.get(part_id, {}).get(bin_num, 0)
                
                if needed > 0:
                    bin_progress[bin_num] = {
                        "needed": needed,
                        "collected": current,
                        "missing": needed - current
                    }
            
            return {
                "total_needed": total_needed,
                "total_collected": total_collected,
                "percent": int((total_collected / total_needed * 100) if total_needed > 0 else 0),
                "bins": bin_progress,
                "overflow": set_data.get("overflow", 0),
                "complete": total_collected >= total_needed
            }
    
    def export_missing_parts(self, set_name: str, filepath: str, inventory_manager) -> bool:
        """Exportiert fehlende Teile als CSV (mit Namen aus Inventory)"""
        try:
            with self.lock:
                if set_name not in self.sets:
                    return False
                
                set_data = self.sets[set_name]
                parts = set_data["parts"]
                collected = set_data["collected"]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Teil-ID", "Name", "Behälter", "Benötigt", "Vorhanden", "Fehlt"])
                
                for part_id, bins in sorted(parts.items()):
                    for bin_num, needed in sorted(bins.items()):
                        current = collected.get(part_id, {}).get(bin_num, 0)
                        missing = needed - current
                        
                        if missing > 0:
                            # Name aus Inventar holen
                            name = inventory_manager.get_part_name(part_id)
                            
                            writer.writerow([
                                part_id,
                                name,
                                bin_num,
                                needed,
                                current,
                                missing
                            ])
            
            return True
            
        except Exception as e:
            print(f"Export-Fehler: {e}")
            return False


# ══════════════════════════════════════════════════════════════
#                    SET-VERWALTUNG GUI (Tab)
# ══════════════════════════════════════════════════════════════

class SetManagementTab(QWidget):
    """Tab für Set-Verwaltung"""
    
    def __init__(self, set_manager, inventory_manager, parent_gui):
        super().__init__()
        self.set_manager = set_manager
        self.inventory_manager = inventory_manager
        self.parent_gui = parent_gui
        
        self.init_ui()
        self.refresh_set_list()
    
    def init_ui(self):
        """UI erstellen"""
        layout = QHBoxLayout()
        
        # === LINKE SEITE: Set-Liste ===
        left_layout = QVBoxLayout()
        
        left_group = QGroupBox("Verfügbare Sets")
        left_group_layout = QVBoxLayout()
        
        self.set_list = QListWidget()
        self.set_list.itemSelectionChanged.connect(self.on_set_selected)
        left_group_layout.addWidget(self.set_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_import = QPushButton("📁 CSV Importieren")
        self.btn_import.clicked.connect(self.import_csv)
        btn_layout.addWidget(self.btn_import)
        
        self.btn_delete = QPushButton("🗑️ Löschen")
        self.btn_delete.clicked.connect(self.delete_set)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)
        
        left_group_layout.addLayout(btn_layout)
        
        # Aktivieren/Deaktivieren
        activate_layout = QHBoxLayout()
        
        self.btn_activate = QPushButton("✅ Aktivieren")
        self.btn_activate.clicked.connect(self.activate_set)
        self.btn_activate.setEnabled(False)
        activate_layout.addWidget(self.btn_activate)
        
        self.btn_deactivate = QPushButton("⏸️ Deaktivieren")
        self.btn_deactivate.clicked.connect(self.deactivate_set)
        self.btn_deactivate.setEnabled(False)
        activate_layout.addWidget(self.btn_deactivate)
        
        left_group_layout.addLayout(activate_layout)
        
        # Reset Button
        self.btn_reset = QPushButton("🔄 Fortschritt zurücksetzen")
        self.btn_reset.clicked.connect(self.reset_set_progress)
        self.btn_reset.setEnabled(False)
        left_group_layout.addWidget(self.btn_reset)
        
        left_group.setLayout(left_group_layout)
        left_layout.addWidget(left_group)
        
        # Aktive Sets Anzeige
        active_group = QGroupBox("Aktive Sets")
        active_layout = QVBoxLayout()
        
        self.active_sets_label = QLabel("Keine Sets aktiv")
        self.active_sets_label.setWordWrap(True)
        active_layout.addWidget(self.active_sets_label)
        
        active_group.setLayout(active_layout)
        left_layout.addWidget(active_group)
        
        layout.addLayout(left_layout, stretch=1)
        
        # === RECHTE SEITE: Fortschritt ===
        right_layout = QVBoxLayout()
        
        right_group = QGroupBox("Set-Fortschritt")
        right_group_layout = QVBoxLayout()
        
        # Set-Name
        self.lbl_set_name = QLabel("Kein Set ausgewählt")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.lbl_set_name.setFont(font)
        self.lbl_set_name.setAlignment(Qt.AlignCenter)
        right_group_layout.addWidget(self.lbl_set_name)
        
        # Gesamt-Fortschritt
        self.progress_total = QProgressBar()
        self.progress_total.setTextVisible(True)
        self.progress_total.setFormat("%p% (%v/%m Teile)")
        right_group_layout.addWidget(self.progress_total)
        
        # Behälter-Fortschritt
        self.bins_table = QTableWidget(0, 4)
        self.bins_table.setHorizontalHeaderLabels(["Behälter", "Benötigt", "Vorhanden", "Status"])
        self.bins_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_group_layout.addWidget(self.bins_table)
        
        # Overflow
        self.lbl_overflow = QLabel("Überschuss: 0 Teile")
        self.lbl_overflow.setAlignment(Qt.AlignCenter)
        right_group_layout.addWidget(self.lbl_overflow)
        
        # Export fehlender Teile
        self.btn_export_missing = QPushButton("📤 Fehlende Teile exportieren")
        self.btn_export_missing.clicked.connect(self.export_missing)
        self.btn_export_missing.setEnabled(False)
        right_group_layout.addWidget(self.btn_export_missing)
        
        right_group.setLayout(right_group_layout)
        right_layout.addWidget(right_group)
        
        layout.addLayout(right_layout, stretch=2)
        
        self.setLayout(layout)
    
    def refresh_set_list(self):
        """Set-Liste aktualisieren"""
        self.set_list.clear()
        
        for set_name in self.set_manager.sets.keys():
            item = QListWidgetItem(set_name)
            
            # Markiere aktive Sets
            if set_name in self.set_manager.active_sets:
                item.setText(f"✅ {set_name}")
                item.setBackground(Qt.darkGreen)
            
            self.set_list.addItem(item)
        
        # Aktive Sets Label aktualisieren
        if self.set_manager.active_sets:
            active_text = "\n".join([f"• {name}" for name in self.set_manager.active_sets])
            self.active_sets_label.setText(active_text)
        else:
            self.active_sets_label.setText("Keine Sets aktiv")
    
    def on_set_selected(self):
        """Set wurde ausgewählt"""
        items = self.set_list.selectedItems()
        
        if not items:
            self.btn_delete.setEnabled(False)
            self.btn_activate.setEnabled(False)
            self.btn_deactivate.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self.btn_export_missing.setEnabled(False)
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        self.btn_delete.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.btn_export_missing.setEnabled(True)
        
        # Aktivieren/Deaktivieren Buttons
        if set_name in self.set_manager.active_sets:
            self.btn_activate.setEnabled(False)
            self.btn_deactivate.setEnabled(True)
        else:
            self.btn_activate.setEnabled(True)
            self.btn_deactivate.setEnabled(False)
        
        # Fortschritt anzeigen
        self.show_progress(set_name)
    
    def show_progress(self, set_name: str):
        """Fortschritt für Set anzeigen"""
        progress = self.set_manager.get_progress(set_name)
        
        if not progress:
            return
        
        # Set-Name
        self.lbl_set_name.setText(set_name)
        
        # Gesamt-Fortschritt
        self.progress_total.setMaximum(progress["total_needed"])
        self.progress_total.setValue(progress["total_collected"])
        
        # Behälter-Tabelle
        self.bins_table.setRowCount(0)
        
        for bin_num, data in sorted(progress["bins"].items()):
            row = self.bins_table.rowCount()
            self.bins_table.insertRow(row)
            
            self.bins_table.setItem(row, 0, QTableWidgetItem(f"Behälter {bin_num}"))
            self.bins_table.setItem(row, 1, QTableWidgetItem(str(data["needed"])))
            self.bins_table.setItem(row, 2, QTableWidgetItem(str(data["collected"])))
            
            # Status
            if data["missing"] == 0:
                status = "✅ Komplett"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(Qt.darkGreen)
            elif data["collected"] > 0:
                status = f"⏳ {data['missing']} fehlt"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(Qt.darkYellow)
            else:
                status = f"❌ {data['missing']} fehlt"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(Qt.darkRed)
            
            self.bins_table.setItem(row, 3, status_item)
        
        # Overflow
        self.lbl_overflow.setText(f"Überschuss: {progress['overflow']} Teile")
    
    def import_csv(self):
        """CSV-Datei importieren"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Set-Liste importieren",
            str(Path.home()),
            "CSV-Dateien (*.csv);;Alle Dateien (*.*)"
        )
        
        if not filepath:
            return
        
        success, message = self.set_manager.load_set_from_csv(filepath)
        
        if success:
            QMessageBox.information(self, "Import erfolgreich", message)
            self.refresh_set_list()
            self.parent_gui.add_log(f"✓ {message}")
        else:
            QMessageBox.warning(self, "Import fehlgeschlagen", message)
    
    def delete_set(self):
        """Set löschen"""
        items = self.set_list.selectedItems()
        if not items:
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        reply = QMessageBox.question(
            self, "Set löschen",
            f"Set '{set_name}' wirklich löschen?\n\nAlle Fortschritte gehen verloren!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.set_manager.delete_set(set_name)
            self.refresh_set_list()
            self.parent_gui.add_log(f"Set '{set_name}' gelöscht")
    
    def activate_set(self):
        """Set aktivieren"""
        items = self.set_list.selectedItems()
        if not items:
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        if self.set_manager.activate_set(set_name):
            self.refresh_set_list()
            self.on_set_selected()
            self.parent_gui.add_log(f"✓ Set '{set_name}' aktiviert")
            self.parent_gui.set_mode_active = True
    
    def deactivate_set(self):
        """Set deaktivieren"""
        items = self.set_list.selectedItems()
        if not items:
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        if self.set_manager.deactivate_set(set_name):
            self.refresh_set_list()
            self.on_set_selected()
            self.parent_gui.add_log(f"Set '{set_name}' deaktiviert")
            
            # Wenn keine Sets mehr aktiv, Set-Modus deaktivieren
            if not self.set_manager.active_sets:
                self.parent_gui.set_mode_active = False
    
    def reset_set_progress(self):
        """Set-Fortschritt zurücksetzen"""
        items = self.set_list.selectedItems()
        if not items:
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        reply = QMessageBox.question(
            self, "Fortschritt zurücksetzen",
            f"Fortschritt für '{set_name}' wirklich zurücksetzen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.set_manager.reset_set(set_name):
                self.show_progress(set_name)
                self.parent_gui.add_log(f"Fortschritt für '{set_name}' zurückgesetzt")
    
    def export_missing(self):
        """Fehlende Teile exportieren"""
        items = self.set_list.selectedItems()
        if not items:
            return
        
        set_name = items[0].text().replace("✅ ", "")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"fehlende_teile_{set_name}_{timestamp}.csv"
        default_path = str(Path.home() / default_filename)
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Fehlende Teile exportieren",
            default_path,
            "CSV-Dateien (*.csv);;Alle Dateien (*.*)"
        )
        
        if not filepath:
            return
        
        if not filepath.endswith('.csv'):
            filepath += '.csv'
        
        if self.set_manager.export_missing_parts(set_name, filepath, self.inventory_manager):
            QMessageBox.information(
                self, "Export erfolgreich",
                f"Fehlende Teile exportiert:\n\n{filepath}"
            )
            self.parent_gui.add_log(f"✓ Fehlende Teile exportiert: {filepath}")
        else:
            QMessageBox.warning(self, "Export fehlgeschlagen", "Fehler beim Exportieren!")


# ══════════════════════════════════════════════════════════════
#                    INTEGRATION INS HAUPTPROGRAMM
# ══════════════════════════════════════════════════════════════

"""
INTEGRATION ANLEITUNG:

1. In LegoSorterGUI.__init__() nach self.inventory = ... hinzufügen:
   
   self.set_manager = SetManager()
   self.set_mode_active = False

2. In init_ui() das zentrale Widget mit Tabs erweitern:
   
   # VORHER:
   central = QWidget()
   self.setCentralWidget(central)
   main_layout = QHBoxLayout(central)
   ... (Rest der UI)
   
   # NACHHER:
   central = QWidget()
   self.setCentralWidget(central)
   main_layout = QVBoxLayout(central)
   
   # Tab-Widget erstellen
   self.tabs = QTabWidget()
   
   # Tab 1: Sortier-Modus (bisherige UI)
   sort_tab = QWidget()
   sort_layout = QHBoxLayout()
   ... (bisherige left_layout und right_layout hier einfügen)
   sort_tab.setLayout(sort_layout)
   self.tabs.addTab(sort_tab, "Sortier-Modus")
   
   # Tab 2: Set-Verwaltung (NEU!)
   self.set_tab = SetManagementTab(self.set_manager, self.inventory, self)
   self.tabs.addTab(self.set_tab, "Set-Verwaltung")
   
   main_layout.addWidget(self.tabs)

#3. In perform_scan() die Sortier-Logik erweitern:
   
   # Nach: result = self.api.analyze(img_bytes)
   
   if result.get("success"):
       part_id = result["id"]
       name = result["name"]
       category = categorize_part(part_id, name)
       
       # SET-MODUS: Behälter basierend auf Set-Liste bestimmen
       if self.set_mode_active and self.set_manager.active_sets:
           bin_number = self.set_manager.get_bin_for_part(part_id, NUM_BINS)
           
           # Teil als gesammelt markieren
           set_name, is_complete = self.set_manager.add_collected_part(part_id, bin_number)
           
           if is_complete and set_name != "overflow":
               self.signals.log_message.emit(f"🎉 SET KOMPLETT: '{set_name}' ist vollständig!")
           
           # Sortieren zu ermitteltem Behälter
           target_angle = SERVO_BIN_ANGLES[bin_number - 1]
           self.hardware.set_servo_position(target_angle)
           
           # Log
           if set_name == "overflow":
               self.signals.log_message.emit(f"  Teil {part_id} → Behälter {bin_number} (Überschuss)")
           else:
               self.signals.log_message.emit(f"  Teil {part_id} → Behälter {bin_number} (Set: {set_name})")
       
       else:
           # NORMAL-MODUS: Kategorien-basierte Sortierung (wie bisher)
           bin_number = CATEGORY_TO_BIN.get(category, NUM_BINS - 1)
           self.hardware.sort_to_category(category)
       
       # Inventar aktualisieren (immer)
       self.inventory.add_part(part_id, name, category)
       
       # Statistik
       self.signals.stats_updated.emit()
       
       # Fortschritt aktualisieren (wenn Set-Tab sichtbar)
       if hasattr(self, 'set_tab') and self.tabs.currentWidget() == self.set_tab:
           QTimer.singleShot(100, self.set_tab.on_set_selected)

#4. Timer für Set-Tab-Updates hinzufügen (in setup_timers()):
   
   # Set-Tab Update Timer (nur wenn Tab aktiv)
   self.set_update_timer = QTimer()
   self.set_update_timer.timeout.connect(self.update_set_tab)
   self.set_update_timer.start(1000)  # Jede Sekunde

#5. Update-Funktion hinzufügen:
   
   def update_set_tab(self):
       '''Set-Tab aktualisieren wenn sichtbar'''
       if hasattr(self, 'set_tab') and hasattr(self, 'tabs'):
           if self.tabs.currentWidget() == self.set_tab:
               items = self.set_tab.set_list.selectedItems()
               if items:
                   set_name = items[0].text().replace("✅ ", "")
                   self.set_tab.show_progress(set_name)

#6. Import datetime hinzufügen (am Anfang der Datei):
   
   #from datetime import datetime
"""

# ══════════════════════════════════════════════════════════════
#                    BEISPIEL CSV-DATEIEN
# ══════════════════════════════════════════════════════════════

"""
BEISPIEL 1: Einfaches Set
═════════════════════════════════════════════════════════════════
Datei: lego_city_60215.csv

SET_NAME: LEGO City 60215 - Feuerwehr-Station
Teil-ID,Anzahl,Behälter
3001,10,1
3004,15,1
3024,8,2
3070,12,2
3040,6,3
32062,4,4
60478,2,4
3023,20,5

═════════════════════════════════════════════════════════════════

BEISPIEL 2: Komplexes Set mit mehreren Behältern pro Teil
═════════════════════════════════════════════════════════════════
Datei: custom_project.csv

SET_NAME: Mein Custom Projekt
Teil-ID,Anzahl,Behälter
3001,5,1
3001,5,2
3001,10,3
3004,8,1
3024,6,2
3024,6,4
3070,15,5

Erklärung:
- Teil 3001: 5 Stück in Behälter 1, 5 in Behälter 2, 10 in Behälter 3
- Teil 3024: 6 Stück in Behälter 2, 6 in Behälter 4

═════════════════════════════════════════════════════════════════

BEISPIEL 3: Mehrere Sets gleichzeitig
═════════════════════════════════════════════════════════════════
Datei 1: set_a.csv
SET_NAME: Set A - Haus
Teil-ID,Anzahl,Behälter
3001,20,1
3004,15,2
3024,10,3

Datei 2: set_b.csv
SET_NAME: Set B - Auto
Teil-ID,Anzahl,Behälter
3023,25,4
60478,8,5
3070,12,6

Datei 3: set_c.csv
SET_NAME: Set C - Figuren
Teil-ID,Anzahl,Behälter
973,10,7
981,10,8
3626,15,9

→ Alle 3 Sets laden und aktivieren
→ Maschine sortiert automatisch in richtige Behälter
→ Überschüssige Teile in Behälter 10

═════════════════════════════════════════════════════════════════
"""

# ══════════════════════════════════════════════════════════════
#                    VERWENDUNGS-WORKFLOW
# ══════════════════════════════════════════════════════════════

"""
WORKFLOW: Set sammeln
═════════════════════════════════════════════════════════════════

1. CSV-Datei vorbereiten
   ├── Erste Zeile: SET_NAME: Dein Set-Name
   ├── Zweite Zeile: Teil-ID,Anzahl,Behälter
   └── Weitere Zeilen: 3001,10,1

2. In GUI: Tab "Set-Verwaltung" öffnen

3. "📁 CSV Importieren" klicken
   → Datei wählen
   → Set wird geladen und gespeichert

4. Set in Liste auswählen
   → Fortschritt wird angezeigt (alles bei 0)

5. "✅ Aktivieren" klicken
   → Set wird aktiv
   → Name wird grün markiert

6. Zurück zu Tab "Sortier-Modus"

7. Sortiermaschine starten (Automatik [F1])
   → Teile werden gescannt
   → Automatisch in richtigen Behälter sortiert
   → Fortschritt wird getrackt

8. Fortschritt überwachen
   → Tab "Set-Verwaltung" öffnen
   → Set auswählen
   → Fortschritt live sehen

9. Bei Completion
   → Log zeigt: "🎉 SET KOMPLETT: 'Dein Set' ist vollständig!"
   → Notification im GUI

10. Fehlende Teile exportieren
    → "📤 Fehlende Teile exportieren" klicken
    → CSV mit allen fehlenden Teilen wird erstellt
    → Datei z.B. für BrickLink-Bestellung verwenden

═════════════════════════════════════════════════════════════════

TIPPS:
- Mehrere Sets können gleichzeitig aktiv sein
- Überschüssige Teile landen immer in letztem Behälter
- Sets bleiben nach Neustart gespeichert
- Fortschritt kann zurückgesetzt werden
- Export zeigt nur fehlende Teile (nicht vollständige)

═════════════════════════════════════════════════════════════════
"""

# ══════════════════════════════════════════════════════════════
#                    FEHLERBEHANDLUNG
# ══════════════════════════════════════════════════════════════

"""
HÄUFIGE FEHLER UND LÖSUNGEN:
═════════════════════════════════════════════════════════════════

FEHLER: "Keine gültigen Teile in CSV gefunden"
LÖSUNG: 
- Prüfe CSV-Format: Teil-ID,Anzahl,Behälter
- Stelle sicher dass Zahlen in Anzahl/Behälter stehen
- Keine Leerzeichen in Teil-IDs

FEHLER: Set wird nicht aktiviert
LÖSUNG:
- Prüfe ob Set in Liste sichtbar
- Erst Set auswählen, dann "Aktivieren" klicken
- Prüfe Log-Ausgabe

FEHLER: Teile landen alle in Overflow
LÖSUNG:
- Prüfe ob Set aktiviert ist (grünes ✅)
- Prüfe ob Teil-IDs in CSV korrekt sind
- Prüfe ob API korrekte Teil-IDs zurückgibt

FEHLER: Fortschritt wird nicht aktualisiert
LÖSUNG:
- Wechsle kurz zu anderem Tab und zurück
- Set neu auswählen in Liste
- Prüfe ob .lego_sorter/sets/*.json Dateien existieren

═════════════════════════════════════════════════════════════════
"""