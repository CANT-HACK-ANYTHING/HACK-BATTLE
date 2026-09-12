"""Middle desk. The only wire between Hands and Head.

Hands and Head are other processes. They never import each other.
Main never posts an invoice. Brain does.
"""

from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from aegis import ocr
from aegis.learn import BrainSkill
from aegis.lock import Frozen
from aegis.memory import Memory
from aegis.vault import Vault
from aegis.vision import see
from aegis.wire import Wire
import config


class Brain:
    def __init__(self, memory: Memory | None = None) -> None:
        self.memory = memory or Memory()
        self.skill = BrainSkill()
        self.log: list[dict] = []
        self.last_submit = None
        self.posted_ok = 0
        self.history: list[dict] = []
        self.field_order = self.skill.suggest_order(config.WINDOW_TITLE)
        self.wayne = Vault()
        self.hands = Wire(config.ROOT / "aegis" / "hands.py", "hands", config.ROOT)
        self.head = Wire(config.ROOT / "aegis" / "lock.py", "head", config.ROOT)

    def _note(self, src: str, dst: str, what: str, extra: dict | None = None) -> None:
        row = {"from": src, "to": dst, "what": what, **(extra or {})}
        self.log.append(row)
        print(f"    {src:5} → {dst:5}  {what}")
        try:
            log = config.LEARN_DIR / "brain" / "wire.jsonl"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as fh:
                import json as _json
                fh.write(_json.dumps(row) + "\n")
        except OSError:
            pass

    def summaries(self) -> tuple[str, str, str]:
        h = self.hands.call(op="skill_summary").get("summary", "")
        d = self.skill.summary()
        t = self.head.call(op="skill_summary").get("summary", "")
        return h, d, t

    def start_window(self) -> dict:
        self._note("brain", "hands", "open Ledger2005")
        ready = self.hands.call(op="open")
        self.hands.call(op="capture")
        self.memory.ingest_tree(self.memory.load_tree())
        self.last_submit = self.memory.stored_box("submit")
        return ready

    def close(self) -> None:
        try:
            self.hands.call(op="close")
        except Exception:
            pass
        self.hands.close()
        self.head.close()

    def dossier(self, inv: dict, amount_box, unusual: str, vision: dict | None = None) -> dict:
        tree = self.memory.load_tree()
        return {
            "unusual": unusual,
            "window": config.WINDOW_TITLE,
            "invoice": dict(inv),
            "amount_box": list(amount_box) if amount_box else None,
            "glass": str(config.GLASS_PATH),
            "tree": tree,
            "posted_ok": self.posted_ok,
            "history": list(self.history),
            "controls": {name: dict(row) for name, row in self.memory.controls.items()},
            "max_amount": config.MAX_AMOUNT,
            "vision": vision,
        }

    def _packet_for_head(self, src) -> str:
        """Copy pixels into Head's inbox. Head never opens the live window folder."""
        import shutil

        config.HEAD_INBOX.mkdir(parents=True, exist_ok=True)
        dest = config.HEAD_INBOX / "packet.png"
        shutil.copy2(src, dest)
        return str(dest)

    def ask_head(self, dossier: dict):
        self._note("brain", "head", f"unusual:{dossier['unusual']}")
        packet = self._packet_for_head(dossier.get("packet") or config.GLASS_PATH)
        reply = self.head.call(
            op="decide",
            amount_box=dossier["amount_box"],
            file_amount=dossier["invoice"].get("amount"),
            window=dossier["window"],
            vendor=str(dossier["invoice"].get("vendor") or ""),
            glass_path=packet,
            timeout=30.0,
        )
        if reply.get("verdict") == "VETO" or reply.get("ok") is False:
            proof = reply.get("proof") or {"rule": reply.get("error") or "veto", "detail": str(reply)}
            learned = proof.get("learned") or {}
            extra = f" z={learned.get('z')} p_veto={learned.get('p_veto')} n={learned.get('n')}" if learned else ""
            self._note("head", "brain", f"VETO {proof.get('rule')}" + extra)
            raise Frozen(proof.get("rule") or "veto", proof)
        learned = reply.get("learned") or {}
        extra = f" z={learned.get('z')} p_veto={learned.get('p_veto')} n={learned.get('n')}" if learned else ""
        self._note("head", "brain", "ALLOW" + extra)
        return reply

    def apply_veto(self, froze: Frozen) -> dict:
        """Brain writes the freeze. Head only returned a verdict."""
        import json
        import shutil

        config.PROOF_DIR.mkdir(parents=True, exist_ok=True)
        config.FREEZE_PATH.write_text(json.dumps(froze.proof, indent=2), encoding="utf-8")
        if config.GLASS_PATH.exists():
            shutil.copy2(config.GLASS_PATH, config.PROOF_DIR / "snap_FROZEN.png")
        self._note("brain", "hands", "rollback snapshot")
        self.hands.call(op="rollback")
        self._note("brain", "hands", "freeze overlay")
        self.hands.call(
            op="overlay",
            text=froze.proof.get("detail", froze.reason),
            detail=f"hash {froze.proof.get('hash', '')[:16]}  rule={froze.proof.get('rule')}",
        )
        return self.hands.call(op="state")

    def _type_field(self, name: str, value: str) -> dict:
        box = self.memory.find(name)
        hint = self.hands.call(op="suggest_box", name=name)
        if hint.get("hits", 0) >= 3:
            self._note("hands", "brain", f"motor hint {name} hits={hint.get('hits')}")
        self._note("brain", "hands", f"type {name}")
        result = self.hands.call(op="focus_and_type", box=list(box), text=value, name=name)
        if result.get("blocked"):
            raise Frozen("mouse_frozen", {"rule": "mouse_frozen", "detail": "click blocked"})
        return result

    def _find_submit(self):
        tree = self.memory.load_tree()
        live = None
        for ctrl in tree.get("controls", []):
            if ctrl.get("name") == "submit":
                live = tuple(ctrl["box"])
                break
        stored = self.last_submit or self.memory.stored_box("submit")
        if live and stored and live != stored:
            self._note("brain", "brain", "Submit moved — rebound from live tree")
            self.skill.remember_rebind("submit", "live_tree")
            self.memory.remember("submit", config.WINDOW_TITLE, "button", "Submit", "", live)
            return live
        if live:
            return live
        if stored:
            return stored
        raise RuntimeError("Submit vanished from glass")

    def post_one(self, inv: dict) -> dict:
        self.hands.call(op="rpc", cmd="clear")
        self.hands.call(op="capture")
        self.memory.ingest_tree(self.memory.load_tree())
        self.hands.call(op="snapshot_rows")

        values = {
            "invoice_no": inv["invoice_no"],
            "vendor": inv["vendor"],
            "date": inv["date"],
            "amount": str(inv["amount"]),
        }
        order = self.field_order or list(values)
        for field in order:
            self._type_field(field, values[field])

        self.hands.call(op="capture")
        amount_box = self.memory.find("amount")

        prior = self.wayne.tombstone_hit(inv)
        if prior:
            self._note("wayne", "brain", f"tombstone on file ({prior.get('rule')}) — Head still reads the glass")

        hidden = self.wayne.ingest(config.GLASS_PATH, inv["invoice_no"])
        self._note("wayne", "vault", f"held {hidden.name}")
        vision = see(config.GLASS_PATH, amount_box)
        self._note("wayne", "brain", f"saw amount={vision.get('ocr_amount')} via {vision.get('source')}")

        pack = self.dossier(inv, amount_box, unusual="submit", vision=vision)
        pack["packet"] = str(hidden)
        try:
            self.ask_head(pack)
        except Frozen as froze:
            self.skill.remember_order(config.WINDOW_TITLE, list(order), False)
            self.wayne.write_tombstone(inv, froze.proof)
            self._note("wayne", "vault", "tombstone — will not try this harm again")
            raise

        self.wayne.confirm_and_purge(inv["invoice_no"])
        self._note("wayne", "vault", "Head confirmed — picture deleted")

        submit_box = self._find_submit()
        self._note("brain", "hands", "click Submit")
        clicked = self.hands.call(op="click_box", box=list(submit_box), name="submit")
        self.last_submit = tuple(submit_box)
        posted = bool(clicked.get("posted"))
        self.skill.remember_order(config.WINDOW_TITLE, list(order), posted)
        if posted:
            self.posted_ok += 1
            self.history.append({"invoice_no": inv["invoice_no"], "amount": inv["amount"], "posted": True})
        return clicked

    def sabotage(self) -> dict:
        self._note("brain", "hands", "demo: move Submit")
        return self.hands.call(op="sabotage")
