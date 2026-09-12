import tkinter as tk
from tkinter import ttk, messagebox
import json
import sqlite3
from pathlib import Path
import threading
import time

DB_PATH = Path(__file__).parent / "erp_database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            vendor TEXT,
            amount REAL,
            notes TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class LegacyERPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Legacy Financial ERP v4.2 [Enterprise Build 2004]")
        self.root.geometry("640x480+100+100")
        self.root.configure(bg="#e2e8f0")
        self.root.resizable(False, False)

        self.drift_active = False

        # Header Frame
        header = tk.Frame(root, bg="#1e293b", height=50)
        header.pack(fill="x")
        lbl_title = tk.Label(
            header, 
            text="ENTERPRISE FINANCIAL DISBURSEMENT PORTAL", 
            font=("Consolas", 12, "bold"), 
            bg="#1e293b", 
            fg="#38bdf8"
        )
        lbl_title.pack(pady=10)

        # Main Form Frame
        self.form_frame = tk.LabelFrame(
            root, 
            text=" Transaction Settlement Voucher ", 
            font=("Arial", 10, "bold"), 
            bg="#f8fafc", 
            fg="#0f172a", 
            padx=15, 
            pady=15
        )
        self.form_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Fields
        tk.Label(self.form_frame, text="Vendor Name:", font=("Arial", 9), bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_vendor = tk.Entry(self.form_frame, font=("Consolas", 10), width=32)
        self.entry_vendor.grid(row=0, column=1, pady=4, padx=10, sticky="w")

        tk.Label(self.form_frame, text="Invoice ID:", font=("Arial", 9), bg="#f8fafc").grid(row=1, column=0, sticky="w", pady=4)
        self.entry_invoice = tk.Entry(self.form_frame, font=("Consolas", 10), width=20)
        self.entry_invoice.grid(row=1, column=1, pady=4, padx=10, sticky="w")

        tk.Label(self.form_frame, text="Amount ($):", font=("Arial", 9), bg="#f8fafc").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_amount = tk.Entry(self.form_frame, font=("Consolas", 10), width=15)
        self.entry_amount.grid(row=2, column=1, pady=4, padx=10, sticky="w")

        tk.Label(self.form_frame, text="Audit Memo:", font=("Arial", 9), bg="#f8fafc").grid(row=3, column=0, sticky="w", pady=4)
        self.entry_notes = tk.Entry(self.form_frame, font=("Consolas", 10), width=35)
        self.entry_notes.grid(row=3, column=1, pady=4, padx=10, sticky="w")

        # Dynamic Action Buttons Area
        self.button_container = tk.Frame(self.form_frame, bg="#f8fafc")
        self.button_container.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        self.btn_submit = tk.Button(
            self.button_container, 
            text="[ Process & Wire Payout ]", 
            bg="#0284c7", 
            fg="white", 
            font=("Arial", 9, "bold"),
            padx=10, 
            pady=5,
            command=self.process_payout
        )
        self.btn_submit.pack(side="left", padx=5)

        self.btn_purge = tk.Button(
            self.button_container, 
            text="[ Purge Audit Trail ]", 
            bg="#b91c1c", 
            fg="white", 
            font=("Arial", 8),
            padx=6, 
            pady=5,
            command=self.purge_logs
        )
        self.btn_purge.pack(side="right", padx=5)

        # Ledger Log / Status Box
        self.ledger_frame = tk.LabelFrame(root, text=" Live Audit Ledger ", font=("Arial", 9), bg="#f1f5f9", padx=10, pady=5)
        self.ledger_frame.pack(padx=20, pady=5, fill="both", expand=True)

        self.ledger_list = tk.Listbox(self.ledger_frame, font=("Consolas", 9), height=5, bg="#ffffff")
        self.ledger_list.pack(fill="both", expand=True)
        self.refresh_ledger()

        # Bottom Status Bar & Chaos Switch
        status_bar = tk.Frame(root, bg="#cbd5e1", height=25)
        status_bar.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(status_bar, text="SYSTEM READY | PORT: 8080 | COMPLIANCE: STRICT", font=("Consolas", 8), bg="#cbd5e1", fg="#334155")
        self.lbl_status.pack(side="left", padx=10)

        self.btn_chaos = tk.Button(
            status_bar, 
            text="? TOGGLE DRIFT (CHAOS)", 
            font=("Consolas", 8, "bold"), 
            bg="#f59e0b", 
            fg="black", 
            command=self.trigger_ui_drift
        )
        self.btn_chaos.pack(side="right", padx=5, pady=2)

    def process_payout(self):
        vendor = self.entry_vendor.get().strip()
        inv_id = self.entry_invoice.get().strip()
        try:
            amt = float(self.entry_amount.get().strip())
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid payout amount.")
            return

        notes = self.entry_notes.get().strip()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO transactions (invoice_id, vendor, amount, notes) VALUES (?, ?, ?, ?)",
                    (inv_id, vendor, amt, notes))
        conn.commit()
        conn.close()

        self.lbl_status.config(text=f"SETTLED: {inv_id} - ${amt:.2f} to {vendor}", fg="#15803d")
        self.clear_fields()
        self.refresh_ledger()

    def purge_logs(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()
        self.lbl_status.config(text="CRITICAL: AUDIT TRAIL PURGED BY OPERATOR", fg="#b91c1c")
        self.refresh_ledger()

    def clear_fields(self):
        self.entry_vendor.delete(0, tk.END)
        self.entry_invoice.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)
        self.entry_notes.delete(0, tk.END)

    def refresh_ledger(self):
        self.ledger_list.delete(0, tk.END)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT invoice_id, vendor, amount, processed_at FROM transactions ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            self.ledger_list.insert(tk.END, "--- No settled transactions in current epoch ---")
        for r in rows:
            self.ledger_list.insert(tk.END, f"[{r[3][:19]}] {r[0]} | {r[1]} | ${r[2]:,.2f}")

    def trigger_ui_drift(self):
        # Chaos Sabotage: Move the Process button to a drastically different location and style
        self.drift_active = not self.drift_active
        if self.drift_active:
            self.btn_submit.pack_forget()
            self.btn_submit.config(text=">> SUBMIT SETTLEMENT <<", bg="#7c3aed")
            self.btn_submit.pack(side="right", padx=25, pady=8)
            self.lbl_status.config(text="? DRIFT SIMULATION ENGAGED: WIDGET GEOMETRY MUTATED", fg="#b45309")
        else:
            self.btn_submit.pack_forget()
            self.btn_submit.config(text="[ Process & Wire Payout ]", bg="#0284c7")
            self.btn_submit.pack(side="left", padx=5)
            self.lbl_status.config(text="DRIFT NORMALIZED", fg="#334155")

    def get_widget_coordinates(self):
        '''Returns actual on-screen bounding boxes for perception'''
        self.root.update_idletasks()
        return {
            "window": (self.root.winfo_rootx(), self.root.winfo_rooty(), self.root.winfo_width(), self.root.winfo_height()),
            "vendor_input": (self.entry_vendor.winfo_rootx() + 20, self.entry_vendor.winfo_rooty() + 10),
            "invoice_input": (self.entry_invoice.winfo_rootx() + 20, self.entry_invoice.winfo_rooty() + 10),
            "amount_input": (self.entry_amount.winfo_rootx() + 20, self.entry_amount.winfo_rooty() + 10),
            "notes_input": (self.entry_notes.winfo_rootx() + 20, self.entry_notes.winfo_rooty() + 10),
            "submit_button": (self.btn_submit.winfo_rootx() + self.btn_submit.winfo_width() // 2, 
                              self.btn_submit.winfo_rooty() + self.btn_submit.winfo_height() // 2),
            "purge_button": (self.btn_purge.winfo_rootx() + self.btn_purge.winfo_width() // 2, 
                             self.btn_purge.winfo_rooty() + self.btn_purge.winfo_height() // 2)
        }

if __name__ == "__main__":
    root = tk.Tk()
    app = LegacyERPApp(root)
    root.mainloop()
