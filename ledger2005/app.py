#!/usr/bin/env python3
"""Ledger2005 — fake 2005 cash-book window.

Paints itself onto run/glass.png. Speaks JSON-lines on stdin/stdout.
No network. Lives on this machine only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402

FONT_REG = config.FONT_REG
FONT_BOLD = config.FONT_BOLD


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


class Ledger2005:
    def __init__(self) -> None:
        self.w, self.h = config.WINDOW_SIZE
        self.title = config.WINDOW_TITLE
        self.fields = {
            "invoice_no": "",
            "vendor": "",
            "date": "",
            "amount": "",
        }
        self.focused = "invoice_no"
        self.posted: list[dict] = []
        self.row_snapshots: list[list[dict]] = []
        self.overlay: str | None = None
        self.overlay_detail: str | None = None
        self.submit_xy = (48, 278)
        self.submit_size = (156, 42)
        self.field_boxes = {
            "invoice_no": (188, 58, 300, 34),
            "vendor": (188, 106, 480, 34),
            "date": (188, 154, 220, 34),
            "amount": (188, 202, 260, 52),
        }
        self.labels = {
            "invoice_no": ("Invoice #", (28, 64)),
            "vendor": ("Vendor", (28, 112)),
            "date": ("Date", (28, 160)),
            "amount": ("Amount Rs", (28, 216)),
        }
        config.RUN_DIR.mkdir(parents=True, exist_ok=True)
        config.PROOF_DIR.mkdir(parents=True, exist_ok=True)
        self.render()

    # --- geometry -------------------------------------------------
    def submit_box(self) -> tuple[int, int, int, int]:
        x, y = self.submit_xy
        w, h = self.submit_size
        return x, y, w, h

    def _hit(self, x: int, y: int) -> str | None:
        sx, sy, sw, sh = self.submit_box()
        if sx <= x <= sx + sw and sy <= y <= sy + sh:
            return "submit"
        for name, (fx, fy, fw, fh) in self.field_boxes.items():
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                return name
        return None

    # --- paint ----------------------------------------------------
    def render(self) -> None:
        img = Image.new("RGB", (self.w, self.h), "#d4d0c8")
        d = ImageDraw.Draw(img)
        title_f = _font(FONT_BOLD, 16)
        ui_f = _font(FONT_REG, 15)
        ui_b = _font(FONT_BOLD, 15)
        amt_f = _font(FONT_BOLD, 26)
        small = _font(FONT_REG, 12)
        mono = _font(config.FONT_MONO, 13)

        # title bar
        d.rectangle([0, 0, self.w, 32], fill="#0a246a")
        d.rectangle([0, 0, self.w - 1, self.h - 1], outline="#404040")
        d.text((10, 7), "Ledger2005  —  Cash Book  (offline)", font=title_f, fill="white")
        d.rectangle([self.w - 28, 6, self.w - 8, 24], outline="white")
        d.text((self.w - 24, 7), "x", font=small, fill="white")

        # menu strip
        d.rectangle([1, 32, self.w - 2, 52], fill="#ece9d8")
        d.text((10, 36), "File   Edit   Post   Window   Help", font=small, fill="#222")

        # entry panel
        d.rectangle([16, 64, self.w - 16, 340], fill="#ece9d8", outline="#808080")
        d.text((24, 40), "", font=ui_f, fill="#000")

        for name, (label, (lx, ly)) in self.labels.items():
            d.text((lx, ly), label, font=ui_b, fill="#111")
            fx, fy, fw, fh = self.field_boxes[name]
            bg = "#ffffff"
            border = "#0a246a" if self.focused == name else "#404040"
            d.rectangle([fx, fy, fx + fw, fy + fh], fill=bg, outline=border, width=2)
            value = self.fields[name]
            if name == "amount":
                shown = ""
                if value:
                    digits = "".join(ch for ch in value if ch.isdigit())
                    shown = f"{int(digits):,}" if digits else value
                d.text((fx + 10, fy + 12), shown, font=amt_f, fill="#111")
            else:
                d.text((fx + 8, fy + 8), value, font=ui_f, fill="#111")

        sx, sy, sw, sh = self.submit_box()
        d.rectangle([sx, sy, sx + sw, sy + sh], fill="#3d5a80", outline="#1b2838", width=2)
        d.text((sx + 38, sy + 12), "Submit", font=ui_b, fill="white")

        # posted table
        d.rectangle([16, 354, self.w - 16, self.h - 16], fill="#ffffff", outline="#808080")
        d.rectangle([16, 354, self.w - 16, 378], fill="#0a246a")
        d.text((24, 358), "Posted  (this session)", font=ui_b, fill="white")
        header = f"{'No':<14} {'Vendor':<22} {'Date':<12} {'Amount':>10}"
        d.text((24, 386), header, font=mono, fill="#333")
        d.line([24, 404, self.w - 28, 404], fill="#aaa")
        if not self.posted:
            d.text((24, 416), "(empty)", font=mono, fill="#888")
        else:
            y = 412
            for row in self.posted[-9:]:
                line = f"{row['invoice_no']:<14} {row['vendor'][:20]:<22} {row['date']:<12} {int(row['amount_int']):>10}"
                d.text((24, y), line, font=mono, fill="#111")
                y += 20

        img = img.convert("RGBA")
        if self.overlay:
            banner = Image.new("RGBA", (self.w, 110), (140, 0, 0, 230))
            bd = ImageDraw.Draw(banner)
            bd.text((16, 12), "MOUSE FROZEN", font=_font(FONT_BOLD, 22), fill="white")
            bd.text((16, 42), self.overlay[:90], font=_font(FONT_REG, 14), fill="#ffd0d0")
            if self.overlay_detail:
                bd.text((16, 68), self.overlay_detail[:110], font=small, fill="#ffd0d0")
            img.alpha_composite(banner, (0, self.h - 110))

        glass = img.convert("RGB")
        glass.save(config.GLASS_PATH)
        self._write_tree(glass)

    def _write_tree(self, glass: Image.Image) -> None:
        controls = []
        for name, box in self.field_boxes.items():
            controls.append(self._ctrl(glass, name, "edit", self.fields[name], box))
        controls.append(self._ctrl(glass, "submit", "button", "Submit", self.submit_box()))
        tree = {
            "window": self.title,
            "size": [self.w, self.h],
            "focused": self.focused,
            "overlay": self.overlay,
            "posted_count": len(self.posted),
            "controls": controls,
        }
        config.TREE_PATH.write_text(json.dumps(tree, indent=2), encoding="utf-8")

    def _ctrl(self, glass: Image.Image, name: str, role: str, text: str, box) -> dict:
        x, y, w, h = box
        crop = glass.crop((x, y, x + w, y + h))
        digest = hashlib.sha256(crop.tobytes()).hexdigest()[:16]
        return {
            "name": name,
            "role": role,
            "ocr_text": text,
            "box": [x, y, w, h],
            "hash": digest,
        }

    # --- actions --------------------------------------------------
    def click(self, x: int, y: int) -> dict:
        if config.FREEZE_PATH.exists():
            return {"ok": False, "error": "mouse_frozen", "hit": None}
        hit = self._hit(x, y)
        if hit == "submit":
            return self.submit()
        if hit in self.fields:
            self.focused = hit
            self.render()
            return {"ok": True, "hit": hit, "action": "focus"}
        return {"ok": True, "hit": None, "action": "miss"}

    def type_text(self, text: str) -> dict:
        if config.FREEZE_PATH.exists():
            return {"ok": False, "error": "mouse_frozen"}
        if self.focused not in self.fields:
            return {"ok": False, "error": "no_focus"}
        self.fields[self.focused] += text
        self.render()
        return {"ok": True, "field": self.focused, "value": self.fields[self.focused]}

    def key(self, name: str) -> dict:
        if name == "backspace" and self.focused in self.fields:
            self.fields[self.focused] = self.fields[self.focused][:-1]
            self.render()
            return {"ok": True}
        if name in ("f9", "sabotage"):
            return self.move_submit()
        return {"ok": False, "error": "unknown_key"}

    def clear_fields(self) -> dict:
        for k in self.fields:
            self.fields[k] = ""
        self.focused = "invoice_no"
        self.render()
        return {"ok": True}

    def snapshot_rows(self) -> dict:
        self.row_snapshots.append([dict(r) for r in self.posted])
        return {"ok": True, "depth": len(self.row_snapshots)}

    def rollback(self) -> dict:
        if not self.row_snapshots:
            self.posted = []
        else:
            self.posted = [dict(r) for r in self.row_snapshots[-1]]
        self.render()
        return {"ok": True, "posted_count": len(self.posted)}

    def move_submit(self) -> dict:
        # Sabotage: button walks to the far right of the posted panel.
        self.submit_xy = (720, 286)
        self.render()
        return {"ok": True, "submit_box": list(self.submit_box()), "note": "Submit moved"}

    def set_overlay(self, text: str, detail: str = "") -> dict:
        self.overlay = text
        self.overlay_detail = detail
        self.render()
        return {"ok": True}

    def clear_overlay(self) -> dict:
        self.overlay = None
        self.overlay_detail = None
        self.render()
        return {"ok": True}

    def submit(self) -> dict:
        if config.FREEZE_PATH.exists():
            return {"ok": False, "error": "mouse_frozen", "posted": False}
        inv = self.fields["invoice_no"].strip()
        vendor = self.fields["vendor"].strip()
        date = self.fields["date"].strip()
        raw = self.fields["amount"].strip().replace(",", "").replace("Rs", "").replace("₹", "").strip()
        if not (inv and vendor and raw):
            return {"ok": False, "error": "incomplete", "posted": False}
        try:
            amount_int = int(float(raw))
        except ValueError:
            return {"ok": False, "error": "bad_amount", "posted": False}
        row = {
            "invoice_no": inv,
            "vendor": vendor,
            "date": date,
            "amount_int": amount_int,
        }
        self.posted.append(row)
        for k in self.fields:
            self.fields[k] = ""
        self.focused = "invoice_no"
        self.render()
        return {"ok": True, "posted": True, "row": row, "posted_count": len(self.posted)}

    def state(self) -> dict:
        return {
            "ok": True,
            "window": self.title,
            "fields": dict(self.fields),
            "focused": self.focused,
            "submit_box": list(self.submit_box()),
            "posted": list(self.posted),
            "overlay": self.overlay,
            "glass": str(config.GLASS_PATH),
        }

    def handle(self, msg: dict) -> dict:
        cmd = msg.get("cmd")
        if cmd == "ping":
            return {"ok": True, "pong": True}
        if cmd == "click":
            return self.click(int(msg["x"]), int(msg["y"]))
        if cmd == "type":
            return self.type_text(str(msg.get("text", "")))
        if cmd == "key":
            return self.key(str(msg.get("name", "")))
        if cmd == "clear":
            return self.clear_fields()
        if cmd == "submit":
            return self.submit()
        if cmd == "move_submit":
            return self.move_submit()
        if cmd == "snapshot_rows":
            return self.snapshot_rows()
        if cmd == "rollback":
            return self.rollback()
        if cmd == "set_overlay":
            return self.set_overlay(str(msg.get("text", "")), str(msg.get("detail", "")))
        if cmd == "clear_overlay":
            return self.clear_overlay()
        if cmd == "state":
            return self.state()
        if cmd == "render":
            self.render()
            return {"ok": True, "glass": str(config.GLASS_PATH)}
        if cmd == "quit":
            return {"ok": True, "bye": True}
        return {"ok": False, "error": f"unknown_cmd:{cmd}"}


def serve() -> None:
    app = Ledger2005()
    sys.stdout.write(json.dumps({"ok": True, "event": "ready", "glass": str(config.GLASS_PATH)}) + "\n")
    sys.stdout.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"ok": False, "error": "bad_json"}) + "\n")
            sys.stdout.flush()
            continue
        result = app.handle(msg)
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()
        if msg.get("cmd") == "quit":
            return


if __name__ == "__main__":
    serve()
