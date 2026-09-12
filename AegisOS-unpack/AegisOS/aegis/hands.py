"""Hands. The operator.

Does what Brain tickets say. Never imports Head. Never decides.
The only desk allowed to move the pointer.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import config
from aegis.learn import HandsSkill


class LedgerGone(RuntimeError):
    pass


class Hands:
    def __init__(self) -> None:
        self.proc: subprocess.Popen | None = None
        self.skill = HandsSkill()

    def open_app(self) -> dict:
        config.RUN_DIR.mkdir(parents=True, exist_ok=True)
        app = config.LEDGER_DIR / "app.py"
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(app)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(config.ROOT),
        )
        ready = self._readline(timeout=10)
        if not ready.get("ok"):
            err = ""
            if self.proc.stderr:
                err = self.proc.stderr.read()
            raise LedgerGone(f"ledger did not start: {ready} {err}")
        return ready

    def _readline(self, timeout: float = 8.0) -> dict:
        if not self.proc or not self.proc.stdout:
            raise LedgerGone("ledger process missing")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            if self.proc.poll() is not None:
                err = self.proc.stderr.read() if self.proc.stderr else ""
                raise LedgerGone(f"ledger exited {self.proc.returncode}: {err}")
            time.sleep(0.02)
        raise LedgerGone("ledger RPC timeout")

    def rpc(self, **msg) -> dict:
        if not self.proc or not self.proc.stdin:
            raise LedgerGone("ledger process missing")
        if config.FREEZE_PATH.exists() and msg.get("cmd") in {"click", "type", "submit"}:
            return {"ok": False, "error": "mouse_frozen", "blocked": True}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return self._readline()

    def capture(self) -> Path:
        self.rpc(cmd="render")
        return config.GLASS_PATH

    def click(self, x: int, y: int) -> dict:
        if config.FREEZE_PATH.exists():
            return {"ok": False, "error": "mouse_frozen", "blocked": True}
        return self.rpc(cmd="click", x=int(x), y=int(y))

    def click_box(self, box, name: str = "") -> dict:
        x, y, w, h = box
        result = self.click(x + w // 2, y + h // 2)
        self.skill.remember_box(name or "click", box, bool(result.get("ok")))
        return result

    def type_text(self, text: str) -> dict:
        if config.FREEZE_PATH.exists():
            return {"ok": False, "error": "mouse_frozen", "blocked": True}
        return self.rpc(cmd="type", text=text)

    def focus_and_type(self, box, text: str, name: str = "") -> dict:
        hit = self.click_box(box, name=name or "field")
        if not hit.get("ok"):
            self.skill.remember_box(name or "field", box, False)
            return hit
        typed = self.type_text(text)
        self.skill.remember_box(name or "field", box, bool(typed.get("ok")))
        return typed

    def sabotage(self) -> dict:
        return self.rpc(cmd="move_submit")

    def snapshot_rows(self) -> dict:
        return self.rpc(cmd="snapshot_rows")

    def rollback(self) -> dict:
        return self.rpc(cmd="rollback")

    def overlay(self, text: str, detail: str = "") -> dict:
        return self.rpc(cmd="set_overlay", text=text, detail=detail)

    def state(self) -> dict:
        return self.rpc(cmd="state")

    def close(self) -> None:
        if not self.proc:
            return
        try:
            if self.proc.poll() is None and self.proc.stdin:
                self.proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=3)
        except Exception:
            pass
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc = None


def serve() -> None:
    """Own process. Brain talks JSON lines. Head is not imported here."""
    import sys as _sys
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[1]
    if str(root) not in _sys.path:
        _sys.path.insert(0, str(root))

    desk = Hands()
    _sys.stdout.write(json.dumps({"ok": True, "desk": "hands", "pid": __import__("os").getpid()}) + "\n")
    _sys.stdout.flush()
    for line in _sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        op = msg.get("op")
        if op == "quit":
            desk.close()
            _sys.stdout.write(json.dumps({"ok": True, "bye": True}) + "\n")
            _sys.stdout.flush()
            return
        try:
            if op == "open":
                out = desk.open_app()
            elif op == "capture":
                path = desk.capture()
                out = {"ok": True, "glass": str(path)}
            elif op == "rpc":
                out = desk.rpc(**{k: v for k, v in msg.items() if k != "op"})
            elif op == "click_box":
                out = desk.click_box(msg["box"], name=str(msg.get("name") or ""))
            elif op == "focus_and_type":
                out = desk.focus_and_type(msg["box"], str(msg.get("text") or ""), name=str(msg.get("name") or ""))
            elif op == "sabotage":
                out = desk.sabotage()
            elif op == "snapshot_rows":
                out = desk.snapshot_rows()
            elif op == "rollback":
                out = desk.rollback()
            elif op == "overlay":
                out = desk.overlay(str(msg.get("text") or ""), str(msg.get("detail") or ""))
            elif op == "state":
                out = desk.state()
            elif op == "suggest_box":
                hit = desk.skill.suggest_box(str(msg.get("name") or ""))
                out = {"ok": True, "box": list(hit[0]) if hit else None, "hits": hit[1] if hit else 0}
            elif op == "skill_summary":
                desk.skill.db.save()
                out = {"ok": True, "summary": desk.skill.summary()}
            elif op == "close":
                desk.close()
                out = {"ok": True}
            else:
                out = {"ok": False, "error": f"unknown_op:{op}"}
        except Exception as exc:
            out = {"ok": False, "error": str(exc)}
        _sys.stdout.write(json.dumps(out) + "\n")
        _sys.stdout.flush()


if __name__ == "__main__":
    serve()
