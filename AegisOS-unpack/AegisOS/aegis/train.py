#!/usr/bin/env python3
"""Replay each desk's private store into its from-scratch unit.

Does not start Ledger2005. Does not click. CPU only.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aegis.learn import BrainSkill, HandsSkill, HeadSkill


def replay_hands(skill: HandsSkill) -> int:
    n = 0
    for ev in skill.db.data.get("events", []):
        if ev.get("kind") != "motor":
            continue
        box = ev.get("box")
        name = ev.get("name") or "field"
        if not box:
            continue
        skill.net.train_one(skill._x(name, box), 1.0 if ev.get("ok") else 0.0, lr=0.05)
        n += 1
    skill.net.save()
    return n


def replay_brain(skill: BrainSkill) -> int:
    n = 0
    for ev in skill.db.data.get("events", []):
        if ev.get("kind") == "route":
            posted = bool(ev.get("posted"))
            fields = ev.get("fields") or []
            skill.net.train_one([1.0 if posted else 0.0, len(fields) / 4.0, 0.0], 1.0 if posted else 0.0)
            n += 1
        elif ev.get("kind") == "rebind":
            skill.net.train_one([0.0, 1.0, 1.0], 1.0)
            n += 1
    skill.net.save()
    return n


def replay_head(skill: HeadSkill) -> int:
    n = 0
    vendors = skill.db.data.get("stats", {}).get("vendors", {})
    for ev in skill.db.data.get("events", []):
        if ev.get("kind") != "verdict":
            continue
        amount = ev.get("amount")
        vendor = ev.get("vendor") or ""
        y = 1.0 if ev.get("verdict") == "VETO" else 0.0
        skill.net.train_one(skill._x(amount, vendor in vendors), y, lr=0.1)
        n += 1
    skill.net.save()
    return n


def main() -> int:
    hands = HandsSkill()
    brain = BrainSkill()
    head = HeadSkill()
    hn = replay_hands(hands)
    bn = replay_brain(brain)
    tn = replay_head(head)
    print("AegisOS train  —  from-scratch units, this laptop only")
    print(f"  hands replayed {hn:4d}  {hands.summary()}")
    print(f"  brain replayed {bn:4d}  {brain.summary()}")
    print(f"  head  replayed {tn:4d}  {head.summary()}")
    print("  weights: learn/hands/model.json  learn/brain/model.json  learn/head/model.json")
    sample = head.score(48900, "Mehta Imports")
    print(f"  head on 48900: z={sample.get('z')} p_veto={sample.get('p_veto')} unusual={sample.get('unusual')}")
    sample2 = head.score(1250, "Sharma Traders")
    print(f"  head on 1250 : z={sample2.get('z')} p_veto={sample2.get('p_veto')} unusual={sample2.get('unusual')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
