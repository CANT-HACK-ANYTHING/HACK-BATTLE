# tests/test_hypervisor.py
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