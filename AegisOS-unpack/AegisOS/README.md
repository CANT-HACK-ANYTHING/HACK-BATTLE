# AegisOS

Local hands. Local memory. A lock that cannot click.

This laptop still has work that only exists as windows — old ledgers, portals, file dialogs. Macros break when a button moves. Cloud agents see the screen. A single local model will click Submit on a wrong number.

AegisOS stays on this PC. One process may move the mouse. The other only reads the screen and can lock the mouse. We show it posting invoices, surviving a moved button, and refusing a tampered amount with the network unplugged.

Same pattern could apply to a hospital or a bank. Not this weekend. Tonight it is a clerk on one machine.

## What it is

An offline clerk for one folder and one old window.

Three desks. One wire. Hands and Head never speak.

```
invoice / glass
      ↓
   [ Brain ]  ← only middle. Memory lives here.
    ↓     ↓
[ Hands ] [ Head ]
 click     decide
 type      only when unusual
```

- **Hands** — the operator. Screenshot, click, type. Never imports Head. Never decides.
- **Brain** — the middle man. Plans the row, holds the control graph, talks to both sides. Main.py does not post invoices.
- **Head** — silent on usual work. Wakes only when Brain flags something unusual (Submit, bad window, on-screen amount). Reads the whole dossier (glass + OCR + file + history) and returns ALLOW or VETO. Never moves the mouse.

A moved button is Brain’s job (relocalize). A illegal number is Head’s job. Hands stays out of both decisions.

**Wayne’s room (`vault/`)** is Brain’s private folder. Pictures of the glass stay on this laptop. Hands does not open it. Head never lists it. Wayne looks with Pillow on the local PNG. Head ALLOW → picture deleted, receipt hash only. Head VETO → tombstone, Wayne will not try that harm again.

Each desk has its own CPU learner and its own store under `learn/<desk>/db.json`. No GPU. No network. They read yesterday’s outcomes and write today’s back.

| Desk | Skill | What it writes |
| --- | --- | --- |
| Hands | motor | boxes that accepted a type or click |
| Brain | route | field order per window, how often Submit had to be rebound |
| Head | anomaly | running mean of allowed amounts, veto rules. Hard freeze in `config.py` still owns the click. The model only scores how strange a number is. |

Freeze → proof hash → rollback snapshot. Nothing leaves the machine.

## What it is not

Not Epic. Not SWIFT. Not a chatbot. Not a cloud Operator. Not a foundation model. Not “the first computer-use agent.”

| Thing | What it does | Why it is not this |
| --- | --- | --- |
| RPA (UiPath) | Replays recorded clicks | Dies or “heals” selectors. Does not read the pixels and refuse Submit. |
| ChatGPT / Claude | Talks. Cloud computer-use sends the screen away | Needs net. One brain marks its own homework. |
| Local agents | Can click this PC | Still one model with a mouse. No hard freeze from on-screen digits. |

Allowed claim only: two processes, one laptop, no network. Only one process has a mouse. The other reads the glass.

## Demo

`invoices/` is the Sept batch (8 slips). `ledger2005/` is the old cash-book window. This machine has no display server, so the app is its own process and paints the window to a local glass PNG. Hands clicks that glass. Lock OCRs it. Nothing goes to the network.

```bash
python3 main.py
```

What happens:

1. Hands opens Ledger2005 and posts invoices into the cash book.
2. Submit is moved. Memory cannot use the stale box. It searches the live window and the next invoice still posts.
3. INV-2005-08 paints **Rs 48,900** on the glass. Lock OCRs that region (not the file JSON) and freezes before click. Overlay shows what it saw, which rule fired, and the proof hash. Ledger has no bad row.

If that loop is boringly reliable, the project is done.

## Layout

```
aegis/hands.py      # operator — click / type only
aegis/brain.py      # middle — only wire, holds memory
aegis/lock.py       # head — unusual decisions only
aegis/memory.py     # control graph used by Brain
aegis/ocr.py        # Pillow template OCR — amount off glass
aegis/tiny.py       # from-scratch logistic unit (CPU)
aegis/vision.py     # Brain looks at glass (Pillow only)
aegis/vault.py      # Wayne's room — pictures never leave
requirements.txt    # Pillow. Everything else is the stdlib.
aegis/learn.py      # three CPU self-learners + private stores
learn/hands|brain|head/db.json
config.py           # Head rules — no model here
ledger2005/
invoices/
main.py             # launcher. Does not post invoices.
```

Lock threshold is `MAX_AMOUNT = 5000` in `config.py`. Raise it only if you want the clerk to post the Mehta slip.

## Proof after a run

- `run/glass.png` — last frame of the window (freeze banner if the lock fired)
- `run/MOUSE_FROZEN` — rule + OCR + hash
- `run/proofs/` — glass copies and JSON proofs
- `run/memory.json` — control graph
