import tkinter as tk
import json
import threading
import time
from pathlib import Path

from config import PROJECT_ROOT
from mock_system.legacy_erp import LegacyERPApp, DB_PATH
from aegis.hud import MissionControlHUD
from aegis.core import AegisOperator

class AegisMasterDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide root, we'll manage two dedicated windows

        # Window 1: The Legacy Enterprise App
        self.erp_win = tk.Toplevel(self.root)
        self.erp_app = LegacyERPApp(self.erp_win)

        # Window 2: The Ambient Mission Control HUD
        self.hud = MissionControlHUD(parent_root=self.root)

        # Initialize the Aegis Operator
        self.operator = AegisOperator(
            target_app=self.erp_app, 
            hud=self.hud, 
            db_path=DB_PATH
        )

        # Add Demo Control Deck to HUD
        deck = tk.Frame(self.hud.win, bg="#0f172a", pady=6)
        deck.pack(fill="x", side="bottom")

        self.btn_run_demo = tk.Button(
            deck, 
            text="? START LIVE 3-ACT DEMO", 
            font=("Consolas", 10, "bold"), 
            bg="#0284c7", 
            fg="white", 
            padx=12, 
            pady=4,
            command=self.start_demo_thread
        )
        self.btn_run_demo.pack(side="left", padx=10)

        self.btn_reset = tk.Button(
            deck, 
            text="? RESET STAGE", 
            font=("Consolas", 9), 
            bg="#334155", 
            fg="#94a3b8", 
            padx=8, 
            pady=4,
            command=self.reset_demo
        )
        self.btn_reset.pack(side="right", padx=10)

        self.hud.log("=== AEGIS-OS STAGED FOR HACKATHON PRESENTATION ===", "info")
        self.hud.log("Click [START LIVE 3-ACT DEMO] or trigger from terminal.", "info")

    def start_demo_thread(self):
        self.btn_run_demo.config(state="disabled", bg="#1e293b")
        t = threading.Thread(target=self._execute_demo_sequence, daemon=True)
        t.start()

    def _execute_demo_sequence(self):
        invoices_file = PROJECT_ROOT / "mock_system" / "sample_invoices.json"
        with open(invoices_file, "r", encoding="utf-8") as f:
            invoices = json.load(f)

        time.sleep(1.0)
        # =========================================================================
        # ACT I: THE HANDS (Zero-Chat Actuation & Muscle Memory)
        # =========================================================================
        self.hud.log(">>> ACT I: THE HANDS (OS Motor Actuation & Muscle Memory)", "info")
        self.hud.log("Directing agent to process legitimate voucher INV-2026-001...", "info")
        time.sleep(1.0)
        self.operator.execute_directive(invoices[0])

        time.sleep(2.0)

        # =========================================================================
        # ACT II: SELF-LEARNING & ADAPTATION (The Chaos Sabotage)
        # =========================================================================
        self.hud.log(">>> ACT II: SELF-LEARNING & ADAPTATION (Chaos UI Drift)", "warn")
        self.hud.log("Simulating real-world entropy: Mutating ERP button coordinates...", "warn")
        
        # Engage UI Drift
        self.erp_win.after(0, self.erp_app.trigger_ui_drift)
        time.sleep(1.5)

        self.hud.log("Directing agent to process voucher INV-2026-002 on mutated UI...", "info")
        self.operator.execute_directive(invoices[1])

        time.sleep(2.0)

        # =========================================================================
        # ACT III: BOUNDARIES & TRUST (The Deterministic Boundary Defense)
        # =========================================================================
        self.hud.log(">>> ACT III: BOUNDARIES & TRUST (Deterministic Boundary Enclave)", "crit")
        self.hud.log("Attacker payload injected: INV-2026-003 ($48,900 + Purge Logs)", "crit")
        time.sleep(1.2)
        
        self.operator.execute_directive(invoices[2])

        self.hud.log("=== 3-ACT DEMO COMPLETE: ZERO HUMAN SUPERVISION REQUIRED ===", "success")
        self.hud.win.after(0, lambda: self.btn_run_demo.config(state="normal", bg="#0284c7"))

    def reset_demo(self):
        self.erp_app.clear_fields()
        if self.erp_app.drift_active:
            self.erp_app.trigger_ui_drift()
        self.erp_app.refresh_ledger()
        self.hud.set_status("? SYSTEM ARMED", "normal")
        self.hud.log("System reset to pristine initial state.", "info")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    demo = AegisMasterDemo()
    demo.run()
