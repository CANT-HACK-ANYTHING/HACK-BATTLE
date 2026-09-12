#!/usr/bin/env python3
"""Judge pass. Fast tests. No network. Fail loud."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from aegis import ocr
from aegis.lock import Frozen, Lock
from aegis.vault import Vault
from ledger2005.app import Ledger2005
from PIL import Image, ImageDraw, ImageFont


class Fail(Exception):
    pass


def _ok(name: str) -> None:
    print(f"  PASS  {name}")


def isolation() -> None:
    banned = {
        "hands.py": ("aegis.lock", "aegis.vault", "aegis.brain"),
        "lock.py": ("aegis.hands", "aegis.vault", "aegis.brain"),
        "vault.py": ("aegis.hands", "aegis.lock"),
    }
    for fname, bad in banned.items():
        tree = ast.parse((ROOT / "aegis" / fname).read_text(encoding="utf-8"))
        got = []
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                got.append(n.module)
            if isinstance(n, ast.Import):
                got.extend(a.name for a in n.names)
        hit = [m for m in got if m in bad]
        if hit:
            raise Fail(f"{fname} imports {hit}")
    lock_src = (ROOT / "aegis" / "lock.py").read_text(encoding="utf-8")
    if "config.FREEZE_PATH" in lock_src or "config.GLASS_PATH" in lock_src:
        raise Fail("Head must not touch the live freeze file or live glass path")
    _ok("desks do not import each other")


def invoices() -> None:
    files = sorted(config.INVOICES_DIR.glob("INV-2005-*.txt"))
    if len(files) != 8:
        raise Fail(f"need 8 invoices, got {len(files)}")
    text = (config.INVOICES_DIR / "INV-2005-08.txt").read_text(encoding="utf-8")
    if "48900" not in text.replace(",", ""):
        raise Fail("tamper slip missing 48900")
    _ok("eight invoices, tamper slip present")


def amount_pixels() -> None:
    font = ImageFont.truetype(config.FONT_BOLD, 26)
    img = Image.new("RGB", (920, 640), "#d4d0c8")
    d = ImageDraw.Draw(img)
    box = (188, 202, 260, 52)
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill="white", outline="#404040", width=2)
    d.text((x + 10, y + 12), "48,900", font=font, fill="#111")
    seen, raw = ocr.amount_from_region(img, box)
    if seen != 48900:
        raise Fail(f"OCR 48900 -> {seen!r} raw={raw!r}")
    d.rectangle([x, y, x + w, y + h], fill="white", outline="#404040", width=2)
    d.text((x + 10, y + 12), "1,250", font=font, fill="#111")
    seen2, raw2 = ocr.amount_from_region(img, box)
    if seen2 != 1250:
        raise Fail(f"OCR 1250 -> {seen2!r} raw={raw2!r}")
    _ok("amount OCR from pixels")


def head_rules() -> None:
    app = Ledger2005()
    app.fields["invoice_no"] = "INV-2005-01"
    app.fields["vendor"] = "Sharma Traders"
    app.fields["date"] = "2005-09-01"
    app.fields["amount"] = "1250"
    app.render()
    lock = Lock()
    box = app.field_boxes["amount"]
    ok = lock.allow_submit(box, 1250, config.WINDOW_TITLE, vendor="Sharma Traders", glass_path=str(config.GLASS_PATH))
    if not ok.get("ok"):
        raise Fail(f"1250 should ALLOW {ok}")
    app.fields["amount"] = "48900"
    app.render()
    try:
        lock.allow_submit(box, 48900, config.WINDOW_TITLE, vendor="Mehta Imports", glass_path=str(config.GLASS_PATH))
        raise Fail("48900 should VETO")
    except Frozen as froze:
        if froze.proof.get("rule") != "max_amount":
            raise Fail(f"expected max_amount, got {froze.proof}")
        if froze.proof.get("ocr_amount") != 48900:
            raise Fail(f"veto OCR {froze.proof.get('ocr_amount')}")
    _ok("Head ALLOW 1250 / VETO 48900 from glass")


def vault_cycle() -> None:
    v = Vault()
    glass = config.GLASS_PATH
    if not glass.exists():
        Image.new("RGB", (20, 20), "white").save(glass)
        config.GLASS_PATH.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (20, 20), "white").save(glass)
    held = v.ingest(glass, "JUDGE-1")
    if not held.exists():
        raise Fail("ingest failed")
    rec = v.confirm_and_purge("JUDGE-1")
    if held.exists():
        raise Fail("ALLOW must delete the picture")
    if not rec.get("purged"):
        raise Fail("receipt missing")
    v.write_tombstone(
        {"invoice_no": "JUDGE-BAD", "vendor": "X", "amount": 9},
        {"rule": "max_amount", "detail": "x", "hash": "00"},
    )
    hit = v.tombstone_hit({"invoice_no": "JUDGE-BAD", "vendor": "X", "amount": 9})
    if not hit:
        raise Fail("tombstone miss")
    _ok("vault ingest / purge / tombstone")


def main() -> int:
    print("AegisOS judge check")
    tests = (isolation, invoices, amount_pixels, head_rules, vault_cycle)
    try:
        config.RUN_DIR.mkdir(parents=True, exist_ok=True)
        config.PROOF_DIR.mkdir(parents=True, exist_ok=True)
        for fn in tests:
            fn()
    except Fail as exc:
        print(f"  FAIL  {exc}")
        return 1
    print("  ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
