"""
AegisOS Configuration & Boundary Rules Specification
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

MEMORY_DB_PATH = DATA_DIR / "episodic_memory.db"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True, parents=True)

# Deterministic Boundary Hypervisor Rules
SAFETY_BOUNDARIES = {
    "MAX_TRANSACTION_AMOUNT": 5000.00,
    "PROTECTED_PATHS": ["system32", "windows", "system_logs", "audit_trail.db"],
    "PROHIBITED_ACTIONS": ["purge_audit_logs", "format_drive", "override_compliance", "dump_credentials"],
    "MAX_DRIFT_DISTANCE_PX": 300,
    "MUSCLE_MEMORY_MIN_CONFIDENCE": 0.85
}
