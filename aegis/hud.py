import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, Any

class MissionControlHUD:
    def __init__(self, parent_root=None):
        if parent_root:
            self.win = tk.Toplevel(parent_root)
        else:
            self.win = tk.Tk()

        self.win.title("AEGIS-OS :: AMBIENT MISSION CONTROL (ZERO-CHAT)")
        self.win.geometry("540x520+760+100")
        self.win.configure(bg="#090d16")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)

        # Header Title
        header = tk.Frame(self.win, bg="#0f172a", height=50)
        header.pack(fill="x")

        lbl_sys = tk.Label(header, text="AEGIS // AUTONOMOUS OPERATOR HUD", font=("Consolas", 11, "bold"), fg="#38bdf8", bg="#0f172a")
        lbl_sys.pack(side="left", padx=12, pady=10)

        self.pill_status = tk.Label(
            header, 
            text="? SYSTEM ARMED", 
            font=("Consolas", 9, "bold"), 
            fg="#10b981", 
            bg="#13271d", 
            padx=10, 
            pady=3
        )
        self.pill_status.pack(side="right", padx=12, pady=10)

        # Telemetry Gauges Frame
        gauges = tk.Frame(self.win, bg="#090d16", pady=8)
        gauges.pack(fill="x", padx=12)

        # Invariant & Boundary Monitor
        self.lbl_boundary_status = tk.Label(
            gauges, 
            text="HYPERVISOR: BOUNDARY ENCLAVE ACTIVE (MAX $5,000 | ZERO-LEAK)", 
            font=("Consolas", 8, "bold"), 
            fg="#94a3b8", 
            bg="#1e293b", 
            padx=8, 
            pady=4
        )
        self.lbl_boundary_status.pack(fill="x", pady=2)

        self.lbl_memory_status = tk.Label(
            gauges, 
            text="EPISODIC GRAPH: 6 NODES CACHED | MUSCLE MEMORY: 100% | HEALED: 0", 
            font=("Consolas", 8), 
            fg="#38bdf8", 
            bg="#111c2e", 
            padx=8, 
            pady=3
        )
        self.lbl_memory_status.pack(fill="x", pady=2)

        # Live Real-time Telemetry Stream
        lbl_log = tk.Label(self.win, text="? LIVE TELEMETRY & INVARIANT STREAM (NO CHAT)", font=("Consolas", 8, "bold"), fg="#64748b", bg="#090d16")
        lbl_log.pack(anchor="w", padx=12, pady=(10, 2))

        self.stream_box = tk.Text(
            self.win, 
            height=12, 
            bg="#030712", 
            fg="#22c55e", 
            font=("Consolas", 8), 
            insertbackground="#22c55e",
            padx=8, 
            pady=8,
            relief="flat"
        )
        self.stream_box.pack(fill="x", padx=12)
        self.stream_box.tag_configure("warn", foreground="#f59e0b")
        self.stream_box.tag_configure("crit", foreground="#ef4444")
        self.stream_box.tag_configure("info", foreground="#38bdf8")
        self.stream_box.tag_configure("success", foreground="#10b981")

        # Cryptographic Proof-of-Boundary Card Area
        self.card_frame = tk.Frame(self.win, bg="#1e1b4b", padx=10, pady=8)
        self.card_frame.pack(fill="both", expand=True, padx=12, pady=10)

        self.lbl_card_title = tk.Label(
            self.card_frame, 
            text="ZERO-REGRET SAFETY VERIFICATION", 
            font=("Consolas", 9, "bold"), 
            fg="#c7d2fe", 
            bg="#1e1b4b"
        )
        self.lbl_card_title.pack(anchor="w")

        self.lbl_card_details = tk.Label(
            self.card_frame, 
            text="Awaiting high-risk mutation or boundary evaluation...", 
            font=("Consolas", 8), 
            fg="#94a3b8", 
            bg="#1e1b4b",
            justify="left"
        )
        self.lbl_card_details.pack(anchor="w", pady=4)

    def log(self, message: str, tag: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        self.stream_box.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.stream_box.see(tk.END)
        self.win.update_idletasks()

    def set_status(self, text: str, mode: str = "normal"):
        color_map = {
            "normal": ("#10b981", "#13271d"),
            "active": ("#38bdf8", "#0f2e46"),
            "healing": ("#f59e0b", "#362208"),
            "breach": ("#ef4444", "#3b1111")
        }
        fg, bg = color_map.get(mode, color_map["normal"])
        self.pill_status.config(text=text, fg=fg, bg=bg)
        self.win.update_idletasks()

    def update_memory_stats(self, nodes: int, healed: int):
        self.lbl_memory_status.config(
            text=f"EPISODIC GRAPH: {nodes} NODES CACHED | MUSCLE MEMORY ACTIVE | HEALED DRIFTS: {healed}"
        )
        self.win.update_idletasks()

    def render_proof_of_boundary(self, proof: Dict[str, Any]):
        self.card_frame.config(bg="#311313")
        self.lbl_card_title.config(
            text=f"? PROOF-OF-BOUNDARY ENFORCED [{proof.get('proof_id', 'POB-SECURE')}]", 
            fg="#fca5a5", 
            bg="#311313"
        )
        violations_str = "\n? ".join(proof.get("violations", []))
        hash_preview = proof.get("cryptographic_hash", "")[:32] + "..."
        details = (
            f"TARGET ACTION: {proof.get('blocked_action')}\n"
            f"REASON: {violations_str}\n"
            f"INTEGRITY HASH: {hash_preview}\n"
            f"PRE-ACTION STATE: 100% UNTOUCHED (ROLLBACK READY)"
        )
        self.lbl_card_details.config(text=details, fg="#fecaca", bg="#311313")
        self.win.update_idletasks()
