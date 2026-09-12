import sqlite3
import hashlib
import time
import json
from pathlib import Path

DB_FILE = Path(__file__).parent / "enterprise_erp.db"

class EnterpriseDatabase:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._init_schema()
        self._seed_data()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # 1. Vendors table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tax_id TEXT NOT NULL,
                risk_score REAL DEFAULT 0.05,
                compliance_status TEXT DEFAULT 'VERIFIED',
                max_single_payout REAL DEFAULT 5000.00
            )
        ''')

        # 2. Invoices table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id TEXT PRIMARY KEY,
                vendor_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'PENDING',
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT NOT NULL,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # 3. Disbursements (Executed payouts)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS disbursements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT NOT NULL UNIQUE,
                vendor_id TEXT NOT NULL,
                amount REAL NOT NULL,
                processed_by TEXT DEFAULT 'AEGIS_AUTONOMOUS_OPERATOR',
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_hash TEXT NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )
        ''')

        # 4. Tamper-evident Audit Ledger (Cryptographic hash chaining)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT NOT NULL,
                block_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _seed_data(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # Seed Vendors
        vendors = [
            ("VEND-001", "Apex Cloud Systems", "US-EIN-9482910", 0.02, "VERIFIED", 5000.00),
            ("VEND-002", "DataCore Logistics", "US-EIN-8823104", 0.04, "VERIFIED", 5000.00),
            ("VEND-003", "Quantum Hardware Lab", "US-EIN-1102938", 0.01, "VERIFIED", 5000.00),
            ("VEND-666", "GhostShell Syndicate", "UNKNOWN-OFFSHORE", 0.99, "BLACKLISTED", 0.00)
        ]
        cur.executemany('''
            INSERT OR IGNORE INTO vendors (vendor_id, name, tax_id, risk_score, compliance_status, max_single_payout)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', vendors)

        # Seed initial genesis block in audit trail if empty
        cur.execute("SELECT COUNT(*) as cnt FROM audit_trail")
        if cur.fetchone()["cnt"] == 0:
            genesis_manifest = "GENESIS|SYSTEM_INITIALIZATION|2026-09-12"
            genesis_hash = hashlib.sha256(genesis_manifest.encode()).hexdigest()
            cur.execute('''
                INSERT INTO audit_trail (event_type, actor, details, block_hash, prev_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', ("GENESIS", "KERNEL_BOOT", "Audit ledger initialization", genesis_hash, "0"*64))

        conn.commit()
        conn.close()

    def create_invoice(self, invoice_id: str, vendor_id: str, amount: float, memo: str) -> str:
        checksum = hashlib.sha256(f"{invoice_id}|{vendor_id}|{amount:.2f}|{memo}".encode()).hexdigest()
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO invoices (invoice_id, vendor_id, amount, memo, checksum)
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_id, vendor_id, amount, memo, checksum))
        conn.commit()
        conn.close()
        return checksum

    def commit_disbursement(self, invoice_id: str) -> str:
        conn = self.get_connection()
        cur = conn.cursor()

        # Fetch invoice
        cur.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
        inv = cur.fetchone()
        if not inv:
            conn.close()
            raise ValueError(f"Invoice {invoice_id} does not exist.")

        # Compute transaction hash
        raw_tx = f"{inv['invoice_id']}|{inv['vendor_id']}|{inv['amount']}|{time.time()}"
        tx_hash = hashlib.sha256(raw_tx.encode()).hexdigest()

        # Insert disbursement (idempotent replacement on demo replay)
        cur.execute('''
            INSERT OR REPLACE INTO disbursements (invoice_id, vendor_id, amount, transaction_hash)
            VALUES (?, ?, ?, ?)
        ''', (inv["invoice_id"], inv["vendor_id"], inv["amount"], tx_hash))

        # Update invoice status
        cur.execute("UPDATE invoices SET status = 'SETTLED' WHERE invoice_id = ?", (invoice_id,))

        # Append to cryptographic audit trail
        cur.execute("SELECT block_hash FROM audit_trail ORDER BY id DESC LIMIT 1")
        last_block = cur.fetchone()
        prev_hash = last_block["block_hash"] if last_block else "0"*64

        block_payload = f"DISBURSEMENT|{inv['invoice_id']}|{inv['amount']}|{tx_hash}|{prev_hash}"
        curr_hash = hashlib.sha256(block_payload.encode()).hexdigest()

        cur.execute('''
            INSERT INTO audit_trail (event_type, actor, details, block_hash, prev_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', ("DISBURSEMENT", "AEGIS_OPERATOR", f"Settled {invoice_id} for ${inv['amount']:,.2f}", curr_hash, prev_hash))

        conn.commit()
        conn.close()
        return tx_hash

    def get_ledger_state(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT d.id, d.invoice_id, v.name as vendor_name, d.amount, d.processed_at, d.transaction_hash
            FROM disbursements d
            JOIN vendors v ON d.vendor_id = v.vendor_id
            ORDER BY d.id DESC
        ''')
        disbursements = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT COUNT(*) as total_audits, MAX(id) as last_audit_id FROM audit_trail")
        audit_info = dict(cur.fetchone())

        conn.close()
        return {
            "disbursements": disbursements,
            "audit_blocks": audit_info
        }
