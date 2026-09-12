#!/usr/bin/env python3
"""Launcher only. The three desks do the work.

Hands never imports Head. Head never imports Hands.
Brain is the only wire. This file does not post invoices.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from aegis.brain import Brain
from aegis.lock import Frozen
from aegis.memory import Memory


def parse_invoice(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def grab(label: str) -> str:
        m = re.search(rf"{label}\s*:\s*(.+)", text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    amount_raw = grab("Amount INR") or grab("Amount")
    amount_raw = re.sub(r"[^0-9]", "", amount_raw)
    return {
        "path": str(path),
        "invoice_no": grab("No"),
        "vendor": grab("Vendor"),
        "date": grab("Date"),
        "amount": int(amount_raw) if amount_raw else 0,
    }


def load_invoices() -> list[dict]:
    files = sorted(config.INVOICES_DIR.glob("INV-2005-*.txt"))
    if len(files) < 8:
        raise SystemExit(f"expected 8 invoices in {config.INVOICES_DIR}, found {len(files)}")
    return [parse_invoice(p) for p in files]


def banner(msg: str) -> None:
    print()
    print("=" * 64)
    print(msg)
    print("=" * 64)


def _export_run() -> None:
    try:
        config.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        for src in (config.GLASS_PATH, config.TREE_PATH, config.FREEZE_PATH, config.MEMORY_DB):
            if src.exists():
                shutil.copy2(src, config.EXPORT_DIR / src.name)
        proofs = config.EXPORT_DIR / "proofs"
        if config.PROOF_DIR.exists():
            if proofs.exists():
                shutil.rmtree(proofs, ignore_errors=True)
            shutil.copytree(config.PROOF_DIR, proofs)
    except OSError as exc:
        print(f"(export skipped: {exc})")


def main() -> int:
    if config.RUN_DIR.exists():
        shutil.rmtree(config.RUN_DIR, ignore_errors=True)
    config.RUN_DIR.mkdir(parents=True, exist_ok=True)
    config.PROOF_DIR.mkdir(parents=True, exist_ok=True)
    config.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    invoices = load_invoices()
    banner("AegisOS  —  three desks, one wire")
    print("  Hands  = operator. Clicks. Never talks to Head.")
    print("  Brain  = middle. Plans. Holds memory. Only wire.")
    print("  Head   = silent until something unusual. Then decides.")
    print(f"  invoices : {len(invoices)}   max Rs {config.MAX_AMOUNT}   network: off")

    brain = Brain(Memory())
    print(f"  pids     : brain={__import__('os').getpid()}  hands={brain.hands.pid}  head={brain.head.pid}")
    hs, bs, ts = brain.summaries()
    print("  " + hs)
    print("  " + bs)
    print("  " + ts)
    print(f"  wayne    : {brain.wayne.counts()}")

    try:
        ready = brain.start_window()
        print(f"  window   : Ledger2005  glass={ready.get('glass')}")

        banner("usual work — Brain talks to Hands only")
        for inv in invoices:
            print(f"\n  → {inv['invoice_no']}  {inv['vendor']}  Rs {inv['amount']}")

            if brain.posted_ok == config.SABOTAGE_AFTER:
                banner("unusual window — Submit moved, Brain heals, Head stays asleep")
                moved = brain.sabotage()
                print(f"  Submit now at {moved.get('submit_box')}")
                print(f"  stored box stays {list(brain.last_submit) if brain.last_submit else None}")

            try:
                result = brain.post_one(inv)
            except Frozen as froze:
                banner("unusual amount — Brain wakes Head, Hands stays out of the decision")
                print(f"  rule   : {froze.proof.get('rule')}")
                print(f"  why    : {froze.proof.get('detail')}")
                print(f"  hash   : {froze.proof.get('hash')}")
                print(f"  ocr    : {froze.proof.get('ocr_raw')}")
                print(f"  seen   : {froze.proof.get('ocr_amount')}")
                print(f"  file   : {froze.proof.get('file_amount')}")
                state = brain.apply_veto(froze)
                nos = [r["invoice_no"] for r in state.get("posted", [])]
                print(f"  ledger : {len(nos)} rows  {nos}")
                if inv["invoice_no"] in nos:
                    print("  FAIL: tampered row landed")
                    return 1
                print("  ledger has no bad row")
                if froze.proof.get("rule") not in {"max_amount", "pixels_disagree", "wayne_will_not_repeat"}:
                    print(f"  FAIL: unexpected rule {froze.proof.get('rule')}")
                    return 1
                if len(nos) != 7:
                    print(f"  FAIL: expected 7 clean rows, got {len(nos)}")
                    return 1
                print("  Hands never saw Head. Head never moved the mouse.")
                self_hs, self_bs, self_ts = brain.summaries()
                print("  " + self_hs)
                print("  " + self_bs)
                print("  " + self_ts)
                banner("Done.")
                return 0

            if not result.get("posted"):
                print(f"    FAIL post: {result}")
                return 1
            print(f"    posted  ({brain.posted_ok} on ledger)")

        print("expected Head veto on tampered invoice did not fire")
        return 1
    finally:
        brain.close()
        _export_run()


if __name__ == "__main__":
    raise SystemExit(main())
