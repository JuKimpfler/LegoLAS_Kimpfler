import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import pandas as pd

# ==========================================
# HIER DEINEN REBRICKABLE API KEY EINTRAGEN:
API_KEY = "DEIN_REBRICKABLE_API_KEY_HIER"
# ==========================================

def select_save_location():
    file_path = filedialog.asksaveasfilename(
        title="Speicherort für Excel-Datei wählen",
        defaultextension=".xlsx",
        filetypes=[("Excel-Dateien", "*.xlsx")]
    )
    if file_path:
        lbl_excel_path.config(text=file_path)
        app_data['excel_path'] = file_path

def fetch_lego_parts():
    set_num = entry_set_num.get().strip()
    excel_path = app_data.get('excel_path')

    if not set_num or not excel_path:
        messagebox.showwarning("Fehlende Eingaben", "Bitte gib eine Set-Nummer ein und wähle einen Speicherort.")
        return

    if API_KEY == "DEIN_REBRICKABLE_API_KEY_HIER":
        messagebox.showerror("Fehlender API Key", "Bitte trage deinen Rebrickable API Key im Skript ein.")
        return

    # Rebrickable erwartet Set-Nummern im Format "Nummer-1"
    if not set_num.endswith("-1"):
        set_num += "-1"

    btn_start.config(state=tk.DISABLED, text="Lade Daten... (Bitte warten)")
    root.update()

    try:
        parts_data = []
        url = f"https://rebrickable.com/api/v3/lego/sets/{set_num}/parts/"
        headers = {'Authorization': f'key {API_KEY}'}
        params = {'page_size': 1000} 

        while url:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                raise ValueError(f"Set {set_num} wurde auf Rebrickable nicht gefunden.")
            response.raise_for_status()
            
            data = response.json()
            
            for item in data['results']:
                # Ersatzteile ignorieren
                if item['is_spare']:
                    continue
                
                # Werte aus der API ziehen
                part_id = item['part']['part_num']       # Part Nummer
                part_name = item['part']['name']         # Name
                qty = item['quantity']                   # Anzahl
                container = ""                           # Container bleibt leer, da Rebrickable das nicht auf Teile-Ebene trackt
                color_name = item['color']['name']       # Farbe
                
                # Exakt die geforderte Reihenfolge als Liste (ohne Keys/Kopfzeilen-Namen)
                row_data = [part_id, part_name, qty, container, color_name]
                parts_data.append(row_data)
            
            # Nächste Seite laden, falls vorhanden
            url = data.get('next')
            params = None

        if not parts_data:
            raise ValueError("Das Set wurde gefunden, enthält aber keine Teileliste.")

        # In Excel umwandeln und speichern (ohne header/Kopfzeile)
        df = pd.DataFrame(parts_data)
        df.to_excel(excel_path, index=False, header=False, engine='openpyxl')

        messagebox.showinfo("Erfolg", f"Erfolgreich {len(parts_data)} Teile-Positionen für Set {set_num} geladen und gespeichert in:\n{excel_path}")

    except Exception as e:
        messagebox.showerror("Verarbeitungsfehler", f"Ein Fehler ist aufgetreten:\n{str(e)}")
    finally:
        btn_start.config(state=tk.NORMAL, text="Teileliste abrufen")

# --- GUI Setup ---
app_data = {}

root = tk.Tk()
root.title("LEGO Set Teilelisten Extractor")
root.geometry("550x300")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill=tk.BOTH)

lbl_set_num = tk.Label(frame, text="1. LEGO Set-Nummer eingeben (z.B. 42115):", font=("Helvetica", 10, "bold"))
lbl_set_num.pack(anchor="w")
entry_set_num = tk.Entry(frame, width=25, font=("Helvetica", 12))
entry_set_num.pack(pady=(5, 15))

btn_excel = tk.Button(frame, text="2. Excel-Speicherort festlegen", command=select_save_location, width=25)
btn_excel.pack(pady=5)
lbl_excel_path = tk.Label(frame, text="Kein Speicherort ausgewählt", fg="gray", wraplength=500)
lbl_excel_path.pack(pady=(0, 25))

btn_start = tk.Button(frame, text="3. Teileliste abrufen", command=fetch_lego_parts, bg="#0055A5", fg="white", font=("Helvetica", 12, "bold"), pady=5)
btn_start.pack(fill=tk.X)

root.mainloop()