"""Wayne looks at the glass.

Python + Pillow only. Reads pixels on this laptop. Never uploads.
Never calls a hosted model. Never talks to Ollama — Head's freeze
does not depend on a daemon.
"""

from __future__ import annotations

from pathlib import Path

from aegis import ocr


def see(glass: Path, amount_box) -> dict:
    """Read the picture on this machine only."""
    img = ocr.load_glass(glass)
    amount, raw = ocr.amount_from_region(img, amount_box) if amount_box else (None, "")
    return {
        "source": "pillow",
        "ocr_amount": amount,
        "ocr_raw": raw,
    }
