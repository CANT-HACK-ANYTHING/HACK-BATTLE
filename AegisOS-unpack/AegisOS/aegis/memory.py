"""Graph of controls. On miss, search the live window. Never invent a box."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from PIL import Image

import config
from aegis import ocr


class Memory:
    def __init__(self, db_path: Path | None = None) -> None:
        self.path = Path(db_path or config.RUN_DIR / "memory.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.controls: dict[str, dict] = {}
        if self.path.exists():
            try:
                self.controls = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.controls = {}

    def _flush(self) -> None:
        try:
            self.path.write_text(json.dumps(self.controls, indent=2), encoding="utf-8")
        except OSError:
            pass

    def remember(self, name: str, window: str, role: str, ocr_text: str, img_hash: str, box) -> None:
        x, y, w, h = [int(v) for v in box]
        self.controls[name] = {
            "name": name,
            "window": window,
            "role": role,
            "ocr_text": ocr_text,
            "img_hash": img_hash,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "last_seen": time.time(),
        }

    def ingest_tree(self, tree: dict) -> None:
        window = tree.get("window") or config.WINDOW_TITLE
        for ctrl in tree.get("controls", []):
            self.remember(
                ctrl["name"],
                window,
                ctrl.get("role", ""),
                ctrl.get("ocr_text", ""),
                ctrl.get("hash", ""),
                ctrl["box"],
            )
        self._flush()

    def get(self, name: str) -> dict | None:
        row = self.controls.get(name)
        return dict(row) if row else None

    def box(self, name: str) -> tuple[int, int, int, int] | None:
        row = self.get(name)
        if not row:
            return None
        return int(row["x"]), int(row["y"]), int(row["w"]), int(row["h"])

    def stored_box(self, name: str) -> tuple[int, int, int, int] | None:
        return self.box(name)

    def center(self, name: str) -> tuple[int, int] | None:
        b = self.box(name)
        if not b:
            return None
        x, y, w, h = b
        return x + w // 2, y + h // 2

    def load_tree(self) -> dict:
        if not config.TREE_PATH.exists():
            return {}
        return json.loads(config.TREE_PATH.read_text(encoding="utf-8"))

    def relocalize(self, name: str, glass: Image.Image | None = None) -> dict:
        """Find a control again after the UI moved.

        Order: live accessibility tree by name → OCR of the glass for the
        control's last known label → stored box only if the crop hash still
        matches. Never add an offset because a simulator told you.
        """
        tree = self.load_tree()
        for ctrl in tree.get("controls", []):
            if ctrl.get("name") == name:
                self.remember(
                    name,
                    tree.get("window") or config.WINDOW_TITLE,
                    ctrl.get("role", ""),
                    ctrl.get("ocr_text", ""),
                    ctrl.get("hash", ""),
                    ctrl["box"],
                )
                return {"found": True, "how": "live_tree", "control": ctrl, "box": ctrl["box"]}

        wanted = self.get(name)
        label = {
            "submit": "Submit",
            "amount": "Amount",
            "vendor": "Vendor",
            "invoice_no": "Invoice",
            "date": "Date",
        }.get(name, name)

        img = glass if glass is not None else ocr.load_glass(config.GLASS_PATH)
        for word in ocr.word_boxes(img):
            if word["text"].lower() == label.lower():
                box = word["box"]
                if name != "submit":
                    x, y, w, h = box
                    box = [x + w + 20, y - 8, 240, max(h + 16, 34)]
                self.remember(name, config.WINDOW_TITLE, "ocr", word["text"], "", box)
                self._flush()
                return {"found": True, "how": "ocr_search", "control": word, "box": box}

        if wanted:
            stored = (wanted["x"], wanted["y"], wanted["w"], wanted["h"])
            crop = ocr.crop_box(img, stored)
            digest = hashlib.sha256(crop.tobytes()).hexdigest()[:16]
            if digest == wanted.get("img_hash"):
                return {"found": True, "how": "hash_confirm", "box": list(stored)}

        return {"found": False, "how": "miss", "box": None}

    def find(self, name: str, glass: Image.Image | None = None) -> tuple[int, int, int, int]:
        hit = self.relocalize(name, glass)
        if not hit["found"]:
            raise LookupError(f"control not on glass: {name}")
        box = hit["box"]
        return int(box[0]), int(box[1]), int(box[2]), int(box[3])

    def box_still_valid(self, name: str, glass: Image.Image | None = None) -> bool:
        stored = self.get(name)
        if not stored:
            return False
        img = glass if glass is not None else ocr.load_glass(config.GLASS_PATH)
        box = (stored["x"], stored["y"], stored["w"], stored["h"])
        crop = ocr.crop_box(img, box)
        if name == "submit":
            text = ocr.read_text(crop, psm=7).lower()
            return "submit" in text
        digest = hashlib.sha256(crop.tobytes()).hexdigest()[:16]
        return digest == (stored.get("img_hash") or "")
