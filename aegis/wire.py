"""JSON-line wire from Brain to a desk process. No shared objects."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


class WireDead(RuntimeError):
    pass


class Wire:
    def __init__(self, script: Path, name: str, cwd: Path) -> None:
        self.name = name
        env = os.environ.copy()
        env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(cwd),
            env=env,
        )
        ready = self.read(timeout=15)
        if not ready.get("ok"):
            raise WireDead(f"{name} did not start: {ready} {self.err()}")

    @property
    def pid(self) -> int | None:
        return self.proc.pid if self.proc else None

    def err(self) -> str:
        if self.proc.stderr and self.proc.poll() is not None:
            return self.proc.stderr.read()
        return ""

    def read(self, timeout: float = 20.0) -> dict:
        if not self.proc.stdout:
            raise WireDead(f"{self.name} has no stdout")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            if self.proc.poll() is not None:
                raise WireDead(f"{self.name} exited {self.proc.returncode}: {self.err()}")
            time.sleep(0.02)
        raise WireDead(f"{self.name} timeout")

    def call(self, timeout: float = 20.0, **msg) -> dict:
        if not self.proc.stdin:
            raise WireDead(f"{self.name} has no stdin")
        if self.proc.poll() is not None:
            raise WireDead(f"{self.name} dead: {self.err()}")
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return self.read(timeout=timeout)

    def close(self) -> None:
        try:
            if self.proc.poll() is None and self.proc.stdin:
                self.proc.stdin.write(json.dumps({"op": "quit"}) + "\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=3)
        except Exception:
            pass
        if self.proc.poll() is None:
            self.proc.kill()
