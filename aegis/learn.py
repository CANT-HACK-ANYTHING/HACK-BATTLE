"""Three CPU-only self-learners. No GPU. No cloud. No foundation model.

Each desk owns a private store under learn/<desk>/ and writes every
outcome back into it. Next run starts from that store, not from zero.
"""

from __future__ import annotations

import json
import math
import time
from collections import Counter
from pathlib import Path

import config
from aegis.tiny import Unit


def _load(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"events": [], "stats": {}}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        try:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass


class Store:
    def __init__(self, desk: str) -> None:
        self.desk = desk
        self.dir = config.LEARN_DIR / desk
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "db.json"
        self.data = _load(self.path)
        self.data.setdefault("events", [])
        self.data.setdefault("stats", {})

    def record(self, kind: str, payload: dict) -> None:
        self.data["events"].append({"ts": time.time(), "kind": kind, **payload})
        # keep the file lean
        if len(self.data["events"]) > 400:
            self.data["events"] = self.data["events"][-400:]
        if len(self.data["events"]) % 8 == 0:
            _save(self.path, self.data)

    def save(self) -> None:
        _save(self.path, self.data)

    @property
    def n(self) -> int:
        return len(self.data["events"])


def _welford_add(stats: dict, x: float) -> dict:
    n = int(stats.get("n", 0)) + 1
    mean = float(stats.get("mean", 0.0))
    m2 = float(stats.get("m2", 0.0))
    delta = x - mean
    mean += delta / n
    m2 += delta * (x - mean)
    return {"n": n, "mean": mean, "m2": m2}


def _welford_z(stats: dict, x: float) -> float | None:
    n = int(stats.get("n", 0))
    if n < 2:
        return None
    var = float(stats.get("m2", 0.0)) / (n - 1)
    sd = math.sqrt(var) if var > 0 else 0.0
    if sd == 0:
        return 0.0 if x == stats.get("mean") else 99.0
    return abs(x - float(stats["mean"])) / sd


class HandsSkill:
    """Motor memory. Learns which boxes accepted a click or a type."""

    def __init__(self) -> None:
        self.db = Store("hands")
        self.db.data["stats"].setdefault("boxes", {})
        self.db.data["stats"].setdefault("field_hits", {})
        self.net = Unit("hands", dim=6)

    def _x(self, name: str, box) -> list[float]:
        x, y, w, h = [int(v) for v in box]
        keys = ("invoice_no", "vendor", "date", "amount")
        one = [1.0 if name == k else 0.0 for k in keys]
        return [x / 920.0, y / 640.0, *one]

    def suggest_box(self, name: str):
        boxes = self.db.data["stats"].get("boxes", {})
        row = boxes.get(name)
        if not row:
            return None
        return tuple(row["box"]), int(row.get("hits", 0))

    def remember_box(self, name: str, box, ok: bool) -> None:
        if not box:
            return
        box = [int(v) for v in box]
        stats = self.db.data["stats"]
        boxes = stats.setdefault("boxes", {})
        hits = stats.setdefault("field_hits", {})
        if ok:
            prev = boxes.get(name) or {"box": box, "hits": 0}
            if prev["box"] == box:
                prev["hits"] = int(prev.get("hits", 0)) + 1
            else:
                prev = {"box": box, "hits": 1}
            boxes[name] = prev
            hits[name] = int(hits.get(name, 0)) + 1
        self.db.record("motor", {"name": name, "box": box, "ok": ok})
        self.net.train_one(self._x(name, box), 1.0 if ok else 0.0)

    def summary(self) -> str:
        boxes = self.db.data["stats"].get("boxes", {})
        names = ", ".join(f"{k}×{v.get('hits', 0)}" for k, v in boxes.items()) or "empty"
        return (
            f"hands-ai motor n={self.db.n} steps={self.net.steps} "
            f"loss={self.net.loss_ema:.3f}  {names}"
        )


class BrainSkill:
    """Route memory. Learns field order and when a control had to be rebound."""

    DEFAULT_ORDER = ("invoice_no", "vendor", "date", "amount")

    def __init__(self) -> None:
        self.db = Store("brain")
        self.db.data["stats"].setdefault("orders", {})
        self.db.data["stats"].setdefault("rebinds", {})
        self.net = Unit("brain", dim=3)

    def suggest_order(self, window: str) -> list[str]:
        orders = self.db.data["stats"].get("orders", {})
        row = orders.get(window)
        if row and row.get("fields"):
            return list(row["fields"])
        return list(self.DEFAULT_ORDER)

    def remember_order(self, window: str, fields: list[str], posted: bool) -> None:
        orders = self.db.data["stats"].setdefault("orders", {})
        if posted:
            orders[window] = {
                "fields": list(fields),
                "uses": int((orders.get(window) or {}).get("uses", 0)) + 1,
            }
        self.db.record("route", {"window": window, "fields": fields, "posted": posted})
        self.net.train_one([1.0 if posted else 0.0, len(fields) / 4.0, 0.0], 1.0 if posted else 0.0)
        self.db.save()

    def remember_rebind(self, name: str, how: str) -> None:
        rebinds = self.db.data["stats"].setdefault("rebinds", {})
        rec = rebinds.setdefault(name, {})
        rec[how] = int(rec.get(how, 0)) + 1
        self.db.record("rebind", {"name": name, "how": how})
        self.net.train_one([0.0, 1.0, 1.0], 1.0)
        self.db.save()

    def predict_post(self) -> float:
        return self.net.predict([1.0, 1.0, 0.0])

    def summary(self) -> str:
        orders = self.db.data["stats"].get("orders", {})
        rebinds = self.db.data["stats"].get("rebinds", {})
        uses = sum(int(v.get("uses", 0)) for v in orders.values())
        return (
            f"brain-ai routes n={self.db.n} steps={self.net.steps} "
            f"loss={self.net.loss_ema:.3f} uses={uses} rebinds={dict(rebinds)}"
        )


class HeadSkill:
    """Anomaly memory. Learns the shape of allowed amounts. Does not click.

    Hard rules in lock.py still own the veto. This only scores how strange
    a number is against the private history of this Head.
    """

    def __init__(self) -> None:
        self.db = Store("head")
        self.db.data["stats"].setdefault("allow_amount", {"n": 0, "mean": 0.0, "m2": 0.0})
        self.db.data["stats"].setdefault("veto_amount", {"n": 0, "mean": 0.0, "m2": 0.0})
        self.db.data["stats"].setdefault("vendors", {})
        self.db.data["stats"].setdefault("rules", {})
        self.net = Unit("head", dim=3)

    def score(self, amount: int | None, vendor: str = "") -> dict:
        allow = self.db.data["stats"].get("allow_amount", {})
        z = _welford_z(allow, float(amount)) if amount is not None else None
        vendors = self.db.data["stats"].get("vendors", {})
        seen_vendor = vendor in vendors
        unusual = bool(z is not None and z >= 3.0) or (vendor and not seen_vendor and vendors)
        p_veto = self.net.predict(self._x(amount, seen_vendor))
        return {
            "n": int(allow.get("n", 0)),
            "mean": float(allow.get("mean", 0.0)),
            "z": None if z is None else round(z, 2),
            "vendor_known": seen_vendor,
            "unusual": unusual,
            "p_veto": round(p_veto, 3),
        }

    def _x(self, amount: int | None, vendor_known: bool) -> list[float]:
        amt = float(amount or 0)
        return [amt / 10000.0, 1.0 if amt > config.MAX_AMOUNT else 0.0, 1.0 if vendor_known else 0.0]

    def observe(self, amount: int | None, vendor: str, verdict: str, rule: str = "") -> dict:
        stats = self.db.data["stats"]
        if amount is not None:
            key = "allow_amount" if verdict == "ALLOW" else "veto_amount"
            stats[key] = _welford_add(stats.get(key) or {}, float(amount))
        if verdict == "ALLOW" and vendor:
            vendors = stats.setdefault("vendors", {})
            vendors[vendor] = int(vendors.get(vendor, 0)) + 1
        if verdict == "VETO" and rule:
            rules = stats.setdefault("rules", {})
            rules[rule] = int(rules.get(rule, 0)) + 1
        self.db.record(
            "verdict",
            {"amount": amount, "vendor": vendor, "verdict": verdict, "rule": rule},
        )
        vendors = stats.get("vendors", {})
        self.net.train_one(self._x(amount, vendor in vendors), 1.0 if verdict == "VETO" else 0.0)
        self.net.save()
        self.db.save()
        return self.score(amount, vendor)

    def summary(self) -> str:
        allow = self.db.data["stats"].get("allow_amount", {})
        rules = self.db.data["stats"].get("rules", {})
        return (
            f"head-ai anomaly n={self.db.n} steps={self.net.steps} "
            f"loss={self.net.loss_ema:.3f} allow_mean={allow.get('mean', 0):.0f} "
            f"allow_n={allow.get('n', 0)} veto_rules={rules}"
        )
