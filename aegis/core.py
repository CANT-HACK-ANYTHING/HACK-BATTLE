import time
from typing import Dict, Any
from pathlib import Path

from aegis.hypervisor import BoundaryHypervisor, PolicyDisposition
from aegis.memory import EpisodicMemoryGraph
from aegis.actuator import OSActuator
from aegis.perception import VisionPerception
from aegis.hud import MissionControlHUD

class AegisOperator:
    def __init__(self, target_app, hud: MissionControlHUD, db_path: Path):
        self.target_app = target_app
        self.hud = hud
        self.hypervisor = BoundaryHypervisor(target_db_path=db_path)
        self.memory = EpisodicMemoryGraph()
        self.actuator = OSActuator()
        self.perception = VisionPerception(target_app_instance=target_app)
        
        self._bootstrap_initial_memory()

    def _bootstrap_initial_memory(self):
        '''Initializes base muscle memory from perception'''
        coords = self.perception.scan_environment()
        for element_name, (x, y) in coords.items():
            self.memory.register_or_update_node(element_name, "LegacyERP", x, y)
        self.hud.log(f"Initialized muscle memory with {len(coords)} spatial anchors.", "info")

    def execute_directive(self, item: Dict[str, Any]) -> bool:
        inv_id = item.get("invoice_id", "UNKNOWN")
        vendor = item.get("vendor", "UNKNOWN")
        amount = item.get("amount", 0.0)
        action = item.get("action", "approve")

        self.hud.log(f"Received Directive: Settle voucher {inv_id} (${amount:,.2f} -> {vendor})", "info")
        self.hud.set_status("? EVALUATING INVARIANTS", "active")
        time.sleep(0.3)

        # ----------------------------------------------------
        # PILLAR 3: BOUNDARY HYPERVISOR PRE-FLIGHT
        # ----------------------------------------------------
        eval_result = self.hypervisor.evaluate_action(action, item)
        if eval_result.violates_policy:
            self.hud.log(f"? BOUNDARY CONTRACT BREACH DETECTED for {inv_id}!", "crit")
            for r in eval_result.reasons:
                self.hud.log(f"  ? {r}", "crit")
            self.hud.set_status("? BOUNDARY INTERCEPTED", "breach")
            self.hud.render_proof_of_boundary(eval_result.proof_of_boundary)
            return False

        self.hud.log(f"Boundary Invariant Verified. Snapshot created [{eval_result.snapshot_id}].", "success")
        self.hud.set_status("? EXECUTING MOTOR ACTIONS", "active")

        # ----------------------------------------------------
        # PILLAR 1 & 2: SENSES, MEMORY, & HANDS
        # ----------------------------------------------------
        live_coords = self.perception.scan_environment()
        fields_to_fill = [
            ("vendor_field", vendor),
            ("invoice_field", inv_id),
            ("amount_field", f"{amount:.2f}"),
            ("notes_field", item.get("notes", ""))
        ]

        for element_name, val in fields_to_fill:
            cached_pos = self.memory.query_node(element_name)
            current_pos = live_coords.get(element_name, cached_pos)
            
            # Check for drift
            if cached_pos:
                is_drift, dist = self.memory.detect_drift(cached_pos, current_pos)
                if is_drift:
                    self.hud.set_status("? SELF-HEALING MEMORY DRIFT", "healing")
                    self.hud.log(f"DRIFT DETECTED: {element_name} moved by {dist:.1f}px! Self-healing...", "warn")
                    self.memory.record_healing_event(element_name, cached_pos, current_pos, dist)
                    history = self.memory.get_healing_history()
                    self.hud.update_memory_stats(nodes=6, healed=len(history))
                    time.sleep(0.2)
            
            # Actuation
            target_x, target_y = current_pos
            self.actuator.type_into_field(target_x, target_y, str(val))

        # Handle Button Click (Submit or Action)
        btn_element = "submit_button" if action == "approve" else "purge_button"
        cached_btn = self.memory.query_node(btn_element)
        current_btn = live_coords.get(btn_element, cached_btn)

        if cached_btn:
            is_drift, dist = self.memory.detect_drift(cached_btn, current_btn)
            if is_drift:
                self.hud.set_status("? SELF-HEALING MEMORY DRIFT", "healing")
                self.hud.log(f"CRITICAL DRIFT: '{btn_element}' relocated by {dist:.1f}px! Recalibrating spatial path...", "warn")
                self.memory.record_healing_event(btn_element, cached_btn, current_btn, dist)
                history = self.memory.get_healing_history()
                self.hud.update_memory_stats(nodes=6, healed=len(history))
                time.sleep(0.3)

        self.hud.set_status("? MOTOR CLICK: SUBMIT", "active")
        self.actuator.click_at(current_btn[0], current_btn[1])
        time.sleep(0.5)

        self.hud.log(f"? Transaction {inv_id} successfully settled and audited.", "success")
        self.hud.set_status("? SYSTEM ARMED", "normal")
        return True
