"""One-neuron models from base. CPU. No framework.

Each desk owns weights in learn/<desk>/model.json.
Training is online SGD on a logistic unit. This is not a foundation model.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import config


def _sigmoid(z: float) -> float:
    z = max(-20.0, min(20.0, z))
    return 1.0 / (1.0 + math.exp(-z))


class Unit:
    def __init__(self, desk: str, dim: int) -> None:
        self.desk = desk
        self.dim = dim
        self.path = config.LEARN_DIR / desk / "model.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.w = [0.0] * dim
        self.b = 0.0
        self.steps = 0
        self.loss_ema = 0.0
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        w = raw.get("w") or []
        if len(w) == self.dim:
            self.w = [float(v) for v in w]
            self.b = float(raw.get("b", 0.0))
            self.steps = int(raw.get("steps", 0))
            self.loss_ema = float(raw.get("loss_ema", 0.0))

    def save(self) -> None:
        payload = {
            "desk": self.desk,
            "dim": self.dim,
            "w": self.w,
            "b": self.b,
            "steps": self.steps,
            "loss_ema": self.loss_ema,
        }
        try:
            self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    def predict(self, x: list[float]) -> float:
        z = self.b
        for wi, xi in zip(self.w, x):
            z += wi * float(xi)
        return _sigmoid(z)

    def train_one(self, x: list[float], y: float, lr: float = 0.08) -> float:
        y = 1.0 if y else 0.0
        p = self.predict(x)
        err = p - y
        for i in range(self.dim):
            self.w[i] -= lr * err * float(x[i])
        self.b -= lr * err
        loss = -(y * math.log(p + 1e-9) + (1 - y) * math.log(1 - p + 1e-9))
        self.steps += 1
        a = 0.05
        self.loss_ema = (1 - a) * self.loss_ema + a * loss if self.steps > 1 else loss
        if self.steps % 10 == 0:
            self.save()
        return loss
