"""AegisOS lock rules. No LLM on this path."""

from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
# Live glass/proofs go to a temp dir so the clerk is not gated by a flaky bind mount.
# Final frames are copied back to ROOT/run at the end of main.py.
RUN_DIR = Path(tempfile.gettempdir()) / "aegis-os-run"
EXPORT_DIR = ROOT / "run"
INVOICES_DIR = ROOT / "invoices"
LEDGER_DIR = ROOT / "ledger2005"
FONTS_DIR = ROOT / "fonts"
GLASS_PATH = RUN_DIR / "glass.png"
TREE_PATH = RUN_DIR / "tree.json"
FREEZE_PATH = RUN_DIR / "MOUSE_FROZEN"
PROOF_DIR = RUN_DIR / "proofs"
MEMORY_DB = RUN_DIR / "memory.json"
LEDGER_SOCK = RUN_DIR / "ledger.sock"
LEARN_DIR = ROOT / "learn"
VAULT_DIR = ROOT / "vault"
HEAD_INBOX = RUN_DIR / "to_head"  # Brain drops a packet here. Head reads only this.


def font_file(name: str) -> str:
    bundled = FONTS_DIR / name
    if bundled.exists():
        return str(bundled)
    linux = Path("/usr/share/fonts/truetype/dejavu") / name
    if linux.exists():
        return str(linux)
    win = Path(r"C:\Windows\Fonts")
    aliases = {
        "DejaVuSans.ttf": ["arial.ttf", "segoeui.ttf", "calibri.ttf"],
        "DejaVuSans-Bold.ttf": ["arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"],
        "DejaVuSansMono.ttf": ["consola.ttf", "cour.ttf", "arial.ttf"],
    }
    for cand in aliases.get(name, []):
        p = win / cand
        if p.exists():
            return str(p)
    return str(bundled)


FONT_REG = font_file("DejaVuSans.ttf")
FONT_BOLD = font_file("DejaVuSans-Bold.ttf")
FONT_MONO = font_file("DejaVuSansMono.ttf")

# Lock
MAX_AMOUNT = 5000
CURRENCY_PREFIXES = ("₹", "rs", "inr", "rs.")
ALLOWED_WINDOWS = ("Ledger2005",)
ALLOWED_FOLDERS = (str(INVOICES_DIR),)
FORBIDDEN_WINDOW_WORDS = ("mail", "outlook", "gmail", "bank", "swift", "delete")
FORBIDDEN_ACTIONS = ("delete", "send_mail", "wire")
SUBMIT_IF_PIXELS_DISAGREE = False

# Display of the fake 2005 window (pixels)
WINDOW_TITLE = "Ledger2005"
WINDOW_SIZE = (920, 640)

# Demo
SABOTAGE_AFTER = 3  # move Submit after this many successful posts
TAMPER_INVOICE_NO = "INV-2005-08"
