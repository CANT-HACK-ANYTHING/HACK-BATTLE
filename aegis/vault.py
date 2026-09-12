"""Wayne's room. Brain only.

Images of the glass never leave this machine. Hands does not import this
module. Head never lists this folder. After Head ALLOW, the picture is
deleted. After Head VETO, a tombstone stays so Wayne will not try that
harm again.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import config


class VaultDenied(RuntimeError):
    pass


class Vault:
    def __init__(self) -> None:
        self.root = config.VAULT_DIR
        self.inbox = self.root / "inbox"
        self.seen = self.root / "seen"
        self.tombstones = self.root / "tombstones"
        self.receipts = self.root / "receipts"
        self.token = self.root / "WAYNE_ONLY"
        self.index_path = self.root / "INDEX.json"
        for d in (self.root, self.inbox, self.seen, self.tombstones, self.receipts):
            d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass
        if not self.token.exists():
            self.token.write_text(
                "Wayne = Brain. Hands and Head do not open this folder.\n"
                "Pictures stay on this laptop. ALLOW deletes them. VETO leaves a tombstone.\n",
                encoding="utf-8",
            )
        self.rebuild_index()

    def _write_index(self, items: list[dict]) -> None:
        tmp = self.index_path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(items, indent=2), encoding="utf-8")
            tmp.replace(self.index_path)
        except OSError:
            try:
                self.index_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
            except OSError:
                pass

    def load_index(self) -> list[dict]:
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except (OSError, json.JSONDecodeError):
                pass
        return self.rebuild_index()

    def rebuild_index(self) -> list[dict]:
        entries: dict[str, dict] = {}
        for path in sorted(self.tombstones.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            inv_no = str(row.get("invoice_no") or path.stem)
            if inv_no.startswith("JUDGE"):
                continue
            entries[inv_no] = {
                "invoice_no": inv_no,
                "kind": "tombstone",
                "rule": row.get("rule") or "veto",
                "ok": False,
                "hash": row.get("hash") or "",
                "ts": float(row.get("ts") or 0.0),
            }
        for path in sorted(self.receipts.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            inv_no = str(row.get("invoice_no") or path.stem)
            if inv_no.startswith("JUDGE"):
                continue
            entries[inv_no] = {
                "invoice_no": inv_no,
                "kind": "receipt",
                "rule": "ok",
                "ok": True,
                "hash": row.get("glass_sha256") or row.get("hash") or "",
                "ts": float(row.get("ts") or 0.0),
            }
        items = sorted(entries.values(), key=lambda x: (x["ts"], x["invoice_no"]))
        self._write_index(items)
        return items

    def _record_index(self, invoice_no: str, kind: str, rule: str, ok: bool, hash_val: str, ts: float) -> None:
        if invoice_no.startswith("JUDGE"):
            return
        items = self.load_index()
        new_entry = {
            "invoice_no": invoice_no,
            "kind": kind,
            "rule": rule,
            "ok": ok,
            "hash": hash_val,
            "ts": ts,
        }
        for idx, item in enumerate(items):
            if item.get("invoice_no") == invoice_no:
                items[idx] = new_entry
                self._write_index(items)
                return
        items.append(new_entry)
        self._write_index(items)

    def _key(self, invoice_no: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in invoice_no)

    def ingest(self, glass: Path, invoice_no: str) -> Path:
        """Copy the live glass into Wayne's room. Not off-machine."""
        if not glass.exists():
            raise VaultDenied("no glass to hide")
        dest = self.seen / f"{self._key(invoice_no)}.png"
        shutil.copy2(glass, dest)
        try:
            os.chmod(dest, 0o600)
        except OSError:
            pass
        return dest

    def tombstone_hit(self, inv: dict) -> dict | None:
        amount = inv.get("amount")
        vendor = (inv.get("vendor") or "").strip().lower()
        no = inv.get("invoice_no")
        for path in self.tombstones.glob("*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("invoice_no") == no:
                return row
            if row.get("amount") == amount and (row.get("vendor") or "").strip().lower() == vendor:
                return row
        return None

    def write_tombstone(self, inv: dict, proof: dict) -> Path:
        key = self._key(str(inv.get("invoice_no") or "unknown"))
        payload = {
            "invoice_no": inv.get("invoice_no"),
            "vendor": inv.get("vendor"),
            "amount": inv.get("amount"),
            "rule": proof.get("rule"),
            "detail": proof.get("detail"),
            "hash": proof.get("hash"),
            "ts": time.time(),
            "will_not_repeat": True,
        }
        dest = self.tombstones / f"{key}.json"
        dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # keep the last refused picture for Wayne, not for Head
        pic = self.seen / f"{key}.png"
        if pic.exists():
            held = self.tombstones / f"{key}.png"
            try:
                pic.replace(held)
            except OSError:
                shutil.copy2(pic, held)
                pic.unlink(missing_ok=True)
        self._record_index(
            str(inv.get("invoice_no") or "unknown"),
            kind="tombstone",
            rule=proof.get("rule") or "veto",
            ok=False,
            hash_val=proof.get("hash") or "",
            ts=payload["ts"],
        )
        return dest

    def confirm_and_purge(self, invoice_no: str, extra: dict | None = None) -> dict:
        """Head said ALLOW. Delete the picture. Keep only a receipt hash."""
        key = self._key(invoice_no)
        pic = self.seen / f"{key}.png"
        digest = ""
        if pic.exists():
            digest = hashlib.sha256(pic.read_bytes()).hexdigest()
            pic.unlink()
        receipt = {
            "invoice_no": invoice_no,
            "purged": True,
            "glass_sha256": digest,
            "ts": time.time(),
            **(extra or {}),
        }
        rec_path = self.receipts / f"{key}.json"
        rec_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        self._record_index(
            invoice_no,
            kind="receipt",
            rule="ok",
            ok=True,
            hash_val=digest or (extra and extra.get("glass_sha256")) or "",
            ts=receipt["ts"],
        )
        return receipt

    def counts(self) -> dict:
        return {
            "seen": len(list(self.seen.glob("*.png"))),
            "tombstones": len(list(self.tombstones.glob("*.json"))),
            "receipts": len(list(self.receipts.glob("*.json"))),
        }
