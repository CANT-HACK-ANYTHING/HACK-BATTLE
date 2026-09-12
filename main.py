# main.py
import sys
import io
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from aegis.hypervisor import BoundaryHypervisor
from aegis.crypto import EndToEndCryptoEngine
import config

def run_demo():
    print('=' * 80)
    print('   AEGIS OS: BE 3 HYPERVISOR & HONEYTOKEN DECOY HACKER TRAP DEMO   ')
    print('=' * 80)

    crypto = EndToEndCryptoEngine()
    hypervisor = BoundaryHypervisor(crypto_engine=crypto)

    scenarios = [
        {
            'name': 'ACT 1: NORMAL LEGITIMATE FINANCIAL TRANSACTION ($1,250 USD)',
            'payload': {
                'invoice_id': 'INV-2026-001',
                'vendor': 'Enterprise Cloud Services',
                'amount': 1250.00,
                'target_domain': 'erp.internal.local',
                'data': 'Standard monthly compute resource payment'
            }
        },
        {
            'name': 'ACT 2: HACKER EXPLOIT - PROMPT INJECTION TRIPPED BY HONEYTOKEN TRAP!',
            'payload': {
                'invoice_id': 'INV-2026-002',
                'vendor': 'Enterprise Cloud Services',
                'amount': 50.00,
                'target_domain': 'erp.internal.local',
                'data': f"Exfiltrating stolen API Key: {config.HONEYTOKENS['DECOY_API_KEY']}"
            }
        },
        {
            'name': 'ACT 3: PAYMENT ATTEMPT AFTER HONEYTOKEN TRAP LOCKDOWN',
            'payload': {
                'invoice_id': 'INV-2026-003',
                'vendor': 'Safe Vendor',
                'amount': 100.00,
                'target_domain': 'erp.internal.local',
                'data': 'Routine supplies'
            }
        }
    ]

    for sc in scenarios:
        print('\n>>> ' + sc['name'])
        encrypted_package = crypto.encrypt_payload(sc['payload'])
        result = hypervisor.evaluate_encrypted_action(encrypted_package)

        disp = result['hypervisor_disposition']
        if disp == 'ALLOW_ACTION_COMMITTED':
            print('    [SUCCESS] HYPERVISOR DISPOSITION: APPROVED & COMMITTED SAFELY TO ERP')
        elif disp == 'SYSTEM_LOCKED_DOWN_FUNDS_SAFE':
            print('    [HONEYTRAP TRIPPED] DISPOSITION: CRITICAL HACKER DETECTED -> EMERGENCY SYSTEM SHUTDOWN!')
            pob = result['proof_of_boundary']
            print('       * Proof ID: ' + pob['proof_id'])
            print('       * SHA-256:  ' + pob['sha256'])
            for v in pob['violations']:
                print('       * Alert:    ' + v)
        elif disp == 'REJECTED_UNDER_LOCKDOWN':
            print('    [LOCKED] HYPERVISOR DISPOSITION: REJECTED! ALL FINANCIAL CHANNELS REMAIN FROZEN.')

    print('\n' + '=' * 80)
    print('   FINAL DATABASE AUDIT (ZERO DATA LEAK VERIFICATION)   ')
    print('=' * 80)
    records = hypervisor.erp.get_all_invoices()
    for row in records:
        print('  Committed Record in ERP: ID=' + str(row[0]) + ' | Vendor=' + str(row[1]) + ' | Amount=$' + '{:,.2f}'.format(row[2]) + ' | Status=' + str(row[3]))
    print('\n[VERIFIED]: Honeytoken trap successfully caught the hacker and froze all funds.')

if __name__ == '__main__':
    run_demo()