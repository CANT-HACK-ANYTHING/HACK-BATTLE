"""Head. Silent. Talks only to Brain.

Never imports Hands, vault, ledger, or main.
Never writes MOUSE_FROZEN. Never lists the live window folder.
Brain hands it one packet (a picture + a box). Head returns ALLOW or VETO.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import config
from aegis import ocr
from aegis.learn import HeadSkill


class Frozen(Exception):
    def __init__(self, reason: str, proof: dict):
        super().__init__(reason)
        self.reason = reason
        self.proof = proof


class Lock:
    def __init__(self) -> None:
        self.skill = HeadSkill()

    def _hash_proof(self, glass: Path, payload: dict) -> str:
        h = hashlib.sha256()
        if glass.exists():
            h.update(glass.read_bytes())
        h.update(json.dumps(payload, sort_keys=True).encode("utf-8"))
        return h.hexdigest()

    def proof(self, glass: Path, rule: str, detail: str, extra: dict | None = None) -> dict:
        payload = {
            "rule": rule,
            "detail": detail,
            "ts": time.time(),
            "window": config.WINDOW_TITLE,
            **(extra or {}),
        }
        payload["hash"] = self._hash_proof(glass, payload)
        return payload

    def inspect_amount(self, glass: Path, amount_box, file_amount: int | None = None) -> dict:
        img = ocr.load_glass(glass)
        seen, raw = ocr.amount_from_region(img, amount_box)
        return {
            "ocr_raw": raw,
            "ocr_amount": seen,
            "file_amount": file_amount,
            "box": list(amount_box) if amount_box else None,
        }

    def allow_submit(
        self,
        amount_box,
        file_amount: int | None,
        window: str,
        vendor: str = "",
        glass_path: str | None = None,
    ) -> dict:
        glass = Path(glass_path) if glass_path else None
        if glass is None or not glass.exists():
            proof = self.proof(
                Path("/dev/null"),
                "no_packet",
                "Brain sent no picture. Head will not look at the live window.",
            )
            raise Frozen(proof["rule"], proof)

        viewed: dict = {}
        rule = ""
        seen = None
        try:
            if window not in config.ALLOWED_WINDOWS:
                rule = "allowed_windows"
                raise Frozen(rule, self.proof(glass, rule, f"window {window!r} is not allowed"))

            lowered = window.lower()
            for word in config.FORBIDDEN_WINDOW_WORDS:
                if word in lowered:
                    rule = "forbidden_window"
                    raise Frozen(rule, self.proof(glass, rule, f"window matched {word!r}"))

            viewed = self.inspect_amount(glass, amount_box, file_amount)
            seen = viewed["ocr_amount"]
            viewed["learned"] = self.skill.score(seen, vendor)

            if seen is None:
                rule = "ocr_unreadable"
                raise Frozen(
                    rule,
                    self.proof(glass, rule, f"could not read amount off packet ({viewed['ocr_raw']!r})", viewed),
                )

            if seen > config.MAX_AMOUNT:
                rule = "max_amount"
                raise Frozen(
                    rule,
                    self.proof(
                        glass,
                        rule,
                        f"on-screen amount {seen} exceeds max {config.MAX_AMOUNT}",
                        viewed,
                    ),
                )

            if file_amount is not None and seen != int(file_amount):
                if not config.SUBMIT_IF_PIXELS_DISAGREE:
                    rule = "pixels_disagree"
                    raise Frozen(
                        rule,
                        self.proof(glass, rule, f"on-screen {seen} != file {file_amount}", viewed),
                    )

            self.skill.observe(seen, vendor, "ALLOW")
            return {"ok": True, **viewed}
        except Frozen as froze:
            self.skill.observe(seen, vendor, "VETO", rule or froze.proof.get("rule", ""))
            raise


def serve() -> None:
    import sys as _sys
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[1]
    if str(root) not in _sys.path:
        _sys.path.insert(0, str(root))

    head = Lock()
    _sys.stdout.write(json.dumps({"ok": True, "desk": "head", "pid": __import__("os").getpid()}) + "\n")
    _sys.stdout.flush()
    for line in _sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        op = msg.get("op")
        if op == "quit":
            _sys.stdout.write(json.dumps({"ok": True, "bye": True}) + "\n")
            _sys.stdout.flush()
            return
        try:
            if op == "decide":
                try:
                    verdict = head.allow_submit(
                        msg.get("amount_box"),
                        file_amount=msg.get("file_amount"),
                        window=str(msg.get("window") or ""),
                        vendor=str(msg.get("vendor") or ""),
                        glass_path=msg.get("glass_path"),
                    )
                    out = {"ok": True, "verdict": "ALLOW", **verdict}
                except Frozen as froze:
                    out = {"ok": False, "verdict": "VETO", "proof": froze.proof}
            elif op == "skill_summary":
                head.skill.db.save()
                out = {"ok": True, "summary": head.skill.summary()}
            else:
                out = {"ok": False, "error": f"unknown_op:{op}"}
        except Exception as exc:
            out = {"ok": False, "error": str(exc)}
        _sys.stdout.write(json.dumps(out) + "\n")
        _sys.stdout.flush()


if __name__ == "__main__":
    serve()
