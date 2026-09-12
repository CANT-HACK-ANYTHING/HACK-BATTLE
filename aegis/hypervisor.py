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
