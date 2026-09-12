import os

hyp_code = '''# aegis/hypervisor.py
import hashlib, json, uuid
from datetime import datetime, timezone
import config
from mock_system.legacy_erp import MockERP
from aegis.crypto import EndToEndCryptoEngine

class BoundaryHypervisor:
    def __init__(self, crypto_engine: EndToEndCryptoEngine = None):
        self.erp = MockERP()
        self.crypto = crypto_engine or EndToEndCryptoEngine()
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
        proof_data = {'proof_id': proof_id, 'timestamp': timestamp, 'lockdown_event': 'EMERGENCY_SYSTEM_SHUTDOWN', 'reason': reason, 'raw_payload': raw_data}
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
            payload = self.crypto.decrypt_payload(encrypted_package)
        except ValueError as err:
            return self.trigger_system_shutdown(str(err), timestamp, {'encrypted': 'CORRUPTED_CIPHERTEXT'})
        return self.evaluate_action(payload, default_memory)

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
        data_text = str(payload.get('data', '')).lower()
        curr = config.POLICY_RULES['CURRENCY_SYMBOL']
        max_limit = config.POLICY_RULES['MAX_TRANSACTION_AMOUNT']

        if target_domain not in config.POLICY_RULES['ALLOWED_DOMAINS']:
            return self.trigger_system_shutdown(f'LATERAL_MOVEMENT_ATTACK: Agent attempted connection to unauthorized target \\'{target_domain}\\'!', timestamp, payload)

        for keyword in config.POLICY_RULES['RESTRICTED_KEYWORDS']:
            if keyword in data_text:
                return self.trigger_system_shutdown(f'DATA_EXFILTRATION_ATTEMPT: Agent attempted to leak sensitive keyword \\'{keyword}\\'!', timestamp, payload)

        if vendor in config.POLICY_RULES['BLOCKED_VENDORS']:
            violations.append(f'SANCTIONED_VENDOR_DETECTED: \\'{vendor}\\' is on sanctions blacklist!')

        if amount > max_limit:
            violations.append(f'TRANSACTION_CEILING_EXCEEDED: {curr}{amount:,.2f} > {curr}{max_limit:,.2f} (Requires Human Supervisor Override)')

        if violations:
            self.erp.rollback()
            proof_id = f'POB-{uuid.uuid4().hex[:8].upper()}'
            proof_data = {'proof_id': proof_id, 'timestamp': timestamp, 'payload': payload, 'violations': violations}
            return {
                'event_type': 'BOUNDARY_INTERCEPTED',
                'timestamp': timestamp,
                'payload': payload,
                'memory_state': default_memory,
                'hypervisor_disposition': 'INTERCEPT_BOUNDARY_VIOLATION',
                'proof_of_boundary': {'proof_id': proof_id, 'sha256': self.generate_sha256(proof_data), 'violations': violations}
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
'''
with open('aegis_os/aegis/hypervisor.py', 'w', encoding='utf-8') as f:
    f.write(hyp_code)
print('HYP OK')

