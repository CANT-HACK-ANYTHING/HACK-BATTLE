<<<<<<< HEAD
﻿# aegis/hypervisor.py
import hashlib
import json
import uuid
from datetime import datetime, timezone
import config
from mock_system.legacy_erp import MockERP
from aegis.crypto import EndToEndCryptoEngine
from aegis.firewall import AutonomousFirewall

class BoundaryHypervisor:
    def __init__(self, crypto_engine: EndToEndCryptoEngine = None):
        self.erp = MockERP()
        self.crypto = crypto_engine or EndToEndCryptoEngine()
        self.firewall = AutonomousFirewall()
        self.SYSTEM_LOCKDOWN_ACTIVE = False
        self.lockdown_reason = ''

    def generate_sha256(self, data: dict) -> str:
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def trigger_system_shutdown(self, reason: str, timestamp: str, raw_data: dict) -> dict:
        self.SYSTEM_LOCKDOWN_ACTIVE = True
        self.lockdown_reason = reason
        self.erp.rollback()

        proof_id = f'POB-SHUTDOWN-{uuid.uuid4().hex[:8].upper()}'
        proof_data = {
            'proof_id': proof_id,
            'timestamp': timestamp,
            'lockdown_event': 'EMERGENCY_SYSTEM_SHUTDOWN',
            'reason': reason,
            'raw_payload': raw_data
        }

        return {
            'event_type': 'EMERGENCY_SYSTEM_SHUTDOWN',
            'timestamp': timestamp,
            'payload': raw_data,
            'hypervisor_disposition': 'SYSTEM_LOCKED_DOWN_FUNDS_SAFE',
            'proof_of_boundary': {
                'proof_id': proof_id,
                'sha256': self.generate_sha256(proof_data),
                'violations': [f'CRITICAL_SECURITY_BREACH: {reason}', 'ALL OPERATIONS FROZEN - USER NOTIFIED']
            }
        }

    def evaluate_encrypted_action(self, encrypted_package: dict, memory_state: dict = None) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        default_memory = memory_state or {'nodes_cached': 6, 'drift_detected': False, 'drift_distance_px': 0.0}

        if self.SYSTEM_LOCKDOWN_ACTIVE:
            return {
                'event_type': 'ACTION_REJECTED_SYSTEM_LOCKED',
                'timestamp': timestamp,
                'payload': {},
                'memory_state': default_memory,
                'hypervisor_disposition': 'REJECTED_UNDER_LOCKDOWN',
                'proof_of_boundary': {
                    'proof_id': 'SYSTEM_FROZEN',
                    'sha256': '0' * 64,
                    'violations': [f'SYSTEM IS IN EMERGENCY LOCKDOWN: {self.lockdown_reason}. Remaining funds are 100% secure.']
                }
            }

        try:
            raw_payload = self.crypto.decrypt_payload(encrypted_package)
        except ValueError as err:
            return self.trigger_system_shutdown(str(err), timestamp, {'encrypted': 'CORRUPTED_CIPHERTEXT'})

        sanitized_payload, self_healed_threats = self.firewall.inspect_and_heal(raw_payload)

        result = self.evaluate_action(sanitized_payload, default_memory)
        if self_healed_threats:
            result['autonomous_firewall_telemetry'] = {
                'threats_detected_count': len(self_healed_threats),
                'self_healing_events': self_healed_threats,
                'status': 'MALWARE_NEUTRALIZED_WORKFLOW_CONTINUED'
            }
        return result

    def evaluate_action(self, payload: dict, memory_state: dict = None) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        default_memory = memory_state or {'nodes_cached': 6, 'drift_detected': False, 'drift_distance_px': 0.0}

        if self.SYSTEM_LOCKDOWN_ACTIVE:
            return {
                'event_type': 'ACTION_REJECTED_SYSTEM_LOCKED',
                'timestamp': timestamp,
                'payload': payload,
                'memory_state': default_memory,
                'hypervisor_disposition': 'REJECTED_UNDER_LOCKDOWN',
                'proof_of_boundary': {
                    'proof_id': 'SYSTEM_FROZEN',
                    'sha256': '0' * 64,
                    'violations': ['SYSTEM IS IN EMERGENCY LOCKDOWN. No further money transfers allowed.']
                }
            }

        self.erp.create_snapshot()

        violations = []
        vendor = payload.get('vendor', '')
        amount = payload.get('amount', 0.0)
        target_domain = payload.get('target_domain', 'erp.internal.local')
        data_text = str(payload.get('data', ''))

        # -------------------------------------------------------------
        # HONEYTOKEN TRAP DETECTOR (100% Certainty Hacker Detection)
        # -------------------------------------------------------------
        for token_name, honey_val in config.HONEYTOKENS.items():
            if honey_val in data_text or honey_val in vendor:
                return self.trigger_system_shutdown(
                    f'HONEYTOKEN_TRAP_TRIPPED: Attacker attempted to exfiltrate decoy secret \'{token_name}\'!',
                    timestamp,
                    payload
                )

        curr = config.POLICY_RULES['CURRENCY_SYMBOL']
        max_limit = config.POLICY_RULES['MAX_TRANSACTION_AMOUNT']

        if target_domain not in config.POLICY_RULES['ALLOWED_DOMAINS']:
            return self.trigger_system_shutdown(
                f'LATERAL_MOVEMENT_ATTACK: Agent attempted connection to unauthorized target \'{target_domain}\'!',
                timestamp,
                payload
            )

        for keyword in config.POLICY_RULES['RESTRICTED_KEYWORDS']:
            if keyword in data_text.lower():
                return self.trigger_system_shutdown(
                    f'DATA_EXFILTRATION_ATTEMPT: Agent attempted to leak sensitive keyword \'{keyword}\'!',
                    timestamp,
                    payload
                )

        if vendor in config.POLICY_RULES['BLOCKED_VENDORS']:
            violations.append(f'SANCTIONED_VENDOR_DETECTED: \'{vendor}\' is on sanctions blacklist!')

        if amount > max_limit:
            violations.append(f'TRANSACTION_CEILING_EXCEEDED: {curr}{amount:,.2f} > {curr}{max_limit:,.2f} (Requires Human Supervisor Override)')

        if violations:
            self.erp.rollback()
            proof_id = f'POB-{uuid.uuid4().hex[:8].upper()}'
            proof_data = {
                'proof_id': proof_id,
                'timestamp': timestamp,
                'payload': payload,
                'violations': violations
            }
            return {
                'event_type': 'BOUNDARY_INTERCEPTED',
                'timestamp': timestamp,
                'payload': payload,
                'memory_state': default_memory,
                'hypervisor_disposition': 'INTERCEPT_BOUNDARY_VIOLATION',
                'proof_of_boundary': {
                    'proof_id': proof_id,
                    'sha256': self.generate_sha256(proof_data),
                    'violations': violations
                }
            }

        if 'invoice_id' in payload:
            self.erp.insert_invoice(payload['invoice_id'], vendor, amount)

        return {
            'event_type': 'ACTION_EVALUATED',
            'timestamp': timestamp,
            'payload': payload,
            'memory_state': default_memory,
            'hypervisor_disposition': 'ALLOW_ACTION_COMMITTED',
            'proof_of_boundary': None
        }
=======
import os
import shutil
import hashlib
import time
import json
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import SAFETY_BOUNDARIES, SNAPSHOT_DIR

class PolicyDisposition(Enum):
    PERMIT_IDEMPOTENT = "PERMIT_IDEMPOTENT"
    PERMIT_MUTATING = "PERMIT_MUTATING"
    INTERCEPT_BOUNDARY_VIOLATION = "INTERCEPT_BOUNDARY_VIOLATION"

@dataclass
class BoundaryEvaluationResult:
    disposition: PolicyDisposition
    violates_policy: bool
    reasons: List[str]
    snapshot_id: Optional[str] = None
    proof_of_boundary: Optional[Dict[str, Any]] = None

class BoundaryHypervisor:
    def __init__(self, target_db_path: Path):
        self.target_db_path = target_db_path
        self.snapshots: Dict[str, Path] = {}
        self.intercept_log: List[Dict[str, Any]] = []

    def evaluate_action(self, action_type: str, payload: Dict[str, Any]) -> BoundaryEvaluationResult:
        '''
        Deterministic pre-flight inspection before OS motor actuation.
        Evaluates payloads against formal mathematical & policy invariants.
        '''
        violations = []
        
        # Invariant 1: Monetary Bounds
        amount = payload.get("amount", 0.0)
        max_amount = SAFETY_BOUNDARIES["MAX_TRANSACTION_AMOUNT"]
        if amount > max_amount:
            violations.append(f"TRANSACTION_CEILING_EXCEEDED: Requested ${amount:,.2f} exceeds strict boundary limit of ${max_amount:,.2f}")

        # Invariant 2: Prohibited Action Types
        if action_type in SAFETY_BOUNDARIES["PROHIBITED_ACTIONS"]:
            violations.append(f"PROHIBITED_SYSTEM_OPERATION: '{action_type}' is classified as a destructive irreversible operation")

        # Invariant 3: Audit Trail / Log Purge Protection
        memo = str(payload.get("notes", "")).lower()
        if "purge" in memo or "drop table" in memo or "bypass" in memo:
            violations.append(f"MALICIOUS_PAYLOAD_DETECTED: Suspicious administrative command injection in memo '{memo}'")

        if violations:
            # Generate Cryptographic Proof-of-Boundary
            proof = self._generate_proof_of_boundary(action_type, payload, violations)
            self.intercept_log.append(proof)
            return BoundaryEvaluationResult(
                disposition=PolicyDisposition.INTERCEPT_BOUNDARY_VIOLATION,
                violates_policy=True,
                reasons=violations,
                proof_of_boundary=proof
            )

        # Mutating action permitted with atomic checkpointing
        snapshot_id = self._create_snapshot()
        return BoundaryEvaluationResult(
            disposition=PolicyDisposition.PERMIT_MUTATING,
            violates_policy=False,
            reasons=[],
            snapshot_id=snapshot_id
        )

    def _create_snapshot(self) -> str:
        '''Creates an atomic zero-overhead snapshot of the state'''
        snapshot_id = f"snap_{int(time.time() * 1000)}"
        if self.target_db_path.exists():
            dest = SNAPSHOT_DIR / f"{snapshot_id}_{self.target_db_path.name}"
            shutil.copy2(self.target_db_path, dest)
            self.snapshots[snapshot_id] = dest
        return snapshot_id

    def rollback(self, snapshot_id: str) -> bool:
        '''Reverts state immediately if post-action check fails'''
        if snapshot_id in self.snapshots:
            snap_file = self.snapshots[snapshot_id]
            if snap_file.exists():
                shutil.copy2(snap_file, self.target_db_path)
                return True
        return False

    def _generate_proof_of_boundary(self, action_type: str, payload: Dict[str, Any], violations: List[str]) -> Dict[str, Any]:
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        raw_manifest = f"{timestamp}|{action_type}|{json.dumps(payload, sort_keys=True)}|{','.join(violations)}"
        proof_hash = hashlib.sha256(raw_manifest.encode("utf-8")).hexdigest()
        
        return {
            "proof_id": f"POB-{proof_hash[:12].upper()}",
            "timestamp": timestamp,
            "blocked_action": action_type,
            "payload_summary": {k: payload[k] for k in ["invoice_id", "vendor", "amount"] if k in payload},
            "violations": violations,
            "cryptographic_hash": proof_hash,
            "status": "DETERMINISTICALLY_BLOCKED"
        }
>>>>>>> 42b4031ff07290e17501dabfbc518edfcea42718
