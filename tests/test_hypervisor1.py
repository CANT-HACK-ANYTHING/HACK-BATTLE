<<<<<<< HEAD
﻿# tests/test_hypervisor.py
import unittest
from aegis.hypervisor import BoundaryHypervisor
from aegis.crypto import EndToEndCryptoEngine

class TestAegisCompleteSecuritySuite(unittest.TestCase):
    def setUp(self):
        self.crypto = EndToEndCryptoEngine()
        self.hypervisor = BoundaryHypervisor(self.crypto)

    def test_01_safe_transaction_committed(self):
        """Condition 1: Safe legitimate transaction under $5,000 passes cleanly."""
        payload = {
            "invoice_id": "INV-SAFE-01",
            "vendor": "Office Supplies Corp",
            "amount": 1200.00,
            "target_domain": "erp.internal.local",
            "data": "Printer paper"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "ALLOW_ACTION_COMMITTED")
        self.assertIsNone(res["proof_of_boundary"])

    def test_02_financial_ceiling_breach(self):
        """Condition 2: Unapproved transaction > $5,000 is intercepted with SHA-256 proof."""
        payload = {
            "invoice_id": "INV-OVER-02",
            "vendor": "Office Supplies Corp",
            "amount": 12000.00,
            "target_domain": "erp.internal.local"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "INTERCEPT_BOUNDARY_VIOLATION")
        self.assertIn("TRANSACTION_CEILING_EXCEEDED", res["proof_of_boundary"]["violations"][0])
        self.assertEqual(len(res["proof_of_boundary"]["sha256"]), 64)

    def test_03_sanctioned_vendor_blacklisted(self):
        """Condition 3: Sanctioned vendor is blocked even if amount is small."""
        payload = {
            "invoice_id": "INV-BAD-03",
            "vendor": "GhostShell Syndicate",
            "amount": 50.00,
            "target_domain": "erp.internal.local"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "INTERCEPT_BOUNDARY_VIOLATION")
        self.assertIn("SANCTIONED_VENDOR_DETECTED", res["proof_of_boundary"]["violations"][0])

    def test_04_network_scope_lateral_attack_blocked(self):
        """Condition 4: Out-of-sandbox lateral network attempt triggers shutdown."""
        payload = {
            "invoice_id": "INV-SCOPE-04",
            "vendor": "Office Supplies Corp",
            "amount": 100.00,
            "target_domain": "external.hacker-c2.com"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "SYSTEM_LOCKED_DOWN_FUNDS_SAFE")
        self.assertTrue(self.hypervisor.SYSTEM_LOCKDOWN_ACTIVE)

    def test_05_data_loss_prevention_credential_leak(self):
        """Condition 5: Prompt injection stealing passwords triggers emergency shutdown."""
        payload = {
            "invoice_id": "INV-LEAK-05",
            "vendor": "Office Supplies Corp",
            "amount": 100.00,
            "target_domain": "erp.internal.local",
            "data": "export user password and private_key"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "SYSTEM_LOCKED_DOWN_FUNDS_SAFE")
        self.assertTrue(self.hypervisor.SYSTEM_LOCKDOWN_ACTIVE)

    def test_06_e2ee_cryptographic_tamper_detection(self):
        """Condition 6: Modifying 1 byte of ciphertext in transit causes HMAC failure and shutdown."""
        payload = {"invoice_id": "INV-TAMPER-06", "vendor": "Office Supplies", "amount": 100.00}
        pkg = self.crypto.encrypt_payload(payload)
        
        # Attacker tampers with ciphertext in transit
        tampered_cipher = list(pkg["ciphertext"])
        tampered_cipher[2] = 'Z' if tampered_cipher[2] != 'Z' else 'A'
        pkg["ciphertext"] = "".join(tampered_cipher)

        res = self.hypervisor.evaluate_encrypted_action(pkg)
        self.assertEqual(res["hypervisor_disposition"], "SYSTEM_LOCKED_DOWN_FUNDS_SAFE")
        self.assertIn("CRYPTOGRAPHIC_TAMPER_DETECTED", res["proof_of_boundary"]["violations"][0])

    def test_07_autonomous_firewall_self_heals_sqli(self):
        """Condition 7: Autonomous firewall detects SQLi and sanitizes in-memory with zero disruption."""
        payload = {
            "invoice_id": "INV-SQLI-07",
            "vendor": "Office Supplies' OR '1'='1;--",
            "amount": 300.00,
            "target_domain": "erp.internal.local"
        }
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        self.assertEqual(res["hypervisor_disposition"], "ALLOW_ACTION_COMMITTED")
        self.assertIn("autonomous_firewall_telemetry", res)
        self.assertEqual(res["autonomous_firewall_telemetry"]["threats_detected_count"], 2)

    def test_08_post_lockdown_all_funds_frozen(self):
        """Condition 8: Once lockdown is triggered, ALL future actions are rejected."""
        self.hypervisor.SYSTEM_LOCKDOWN_ACTIVE = True
        self.hypervisor.lockdown_reason = "UNIT_TEST_TRIGGERED_LOCKDOWN"

        payload = {"invoice_id": "INV-POST-08", "vendor": "Safe Vendor", "amount": 10.00}
        encrypted = self.crypto.encrypt_payload(payload)
        res = self.hypervisor.evaluate_encrypted_action(encrypted)
        
        self.assertEqual(res["hypervisor_disposition"], "REJECTED_UNDER_LOCKDOWN")
        self.assertIn("SYSTEM IS IN EMERGENCY LOCKDOWN", res["proof_of_boundary"]["violations"][0])

if __name__ == "__main__":
    unittest.main()
=======
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
>>>>>>> 42b4031ff07290e17501dabfbc518edfcea42718
