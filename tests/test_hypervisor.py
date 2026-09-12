import unittest
import json
import sqlite3
from pathlib import Path

from config import SAFETY_BOUNDARIES, PROJECT_ROOT
from aegis.hypervisor import BoundaryHypervisor, PolicyDisposition
from aegis.memory import EpisodicMemoryGraph

class TestAegisSystem(unittest.TestCase):
    def setUp(self):
        self.db_path = PROJECT_ROOT / "mock_system" / "erp_database.db"
        self.hypervisor = BoundaryHypervisor(self.db_path)
        self.memory = EpisodicMemoryGraph(PROJECT_ROOT / "data" / "test_memory.db")

    def test_safe_transaction_permitted(self):
        payload = {
            "invoice_id": "INV-TEST-001",
            "vendor": "Test Vendor",
            "amount": 2500.00,
            "notes": "Valid test transaction"
        }
        res = self.hypervisor.evaluate_action("approve", payload)
        self.assertFalse(res.violates_policy)
        self.assertEqual(res.disposition, PolicyDisposition.PERMIT_MUTATING)
        self.assertIsNotNone(res.snapshot_id)

    def test_over_budget_transaction_blocked(self):
        payload = {
            "invoice_id": "INV-TEST-002",
            "vendor": "Greedy Vendor",
            "amount": 99999.00,
            "notes": "Over budget"
        }
        res = self.hypervisor.evaluate_action("approve", payload)
        self.assertTrue(res.violates_policy)
        self.assertEqual(res.disposition, PolicyDisposition.INTERCEPT_BOUNDARY_VIOLATION)
        self.assertIn("TRANSACTION_CEILING_EXCEEDED", res.reasons[0])
        self.assertIsNotNone(res.proof_of_boundary)
        self.assertIn("POB-", res.proof_of_boundary["proof_id"])

    def test_prohibited_action_blocked(self):
        payload = {
            "invoice_id": "INV-TEST-003",
            "vendor": "Attacker",
            "amount": 100.00,
            "notes": "Purge all records"
        }
        res = self.hypervisor.evaluate_action("purge_audit_logs", payload)
        self.assertTrue(res.violates_policy)
        self.assertEqual(res.disposition, PolicyDisposition.INTERCEPT_BOUNDARY_VIOLATION)

    def test_drift_detection_and_self_healing(self):
        old_pos = (100, 200)
        new_pos = (350, 200) # Drifted by 250px
        
        is_drift, dist = self.memory.detect_drift(old_pos, new_pos)
        self.assertTrue(is_drift)
        self.assertEqual(dist, 250.0)

        # Record healing
        self.memory.record_healing_event("submit_button", old_pos, new_pos, dist)
        history = self.memory.get_healing_history()
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["drift_px"], 250.0)

if __name__ == "__main__":
    unittest.main()
