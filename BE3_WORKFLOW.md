# BE3 workflow — give this to the Head / security person
Paste this whole file into their chat. They implement **only the Head box**.

You are **BE3**. You do not run the clerk. You do not design Hands. You do not own `vault/`.

---

## Full clerk (so you know where you sit)

```
invoices/ + Ledger2005 window
        │
        ▼
     BE1 Hands          click / type / screenshot
        │                 writes glass.png + tree.json
        ▼
     BE2 Brain / Wayne  ONLY WIRE. Offline DBs. Vault.
        │
        │  copies pixels → /tmp/aegis-os-run/to_head/packet.png
        │  sends you one JSON packet
        ▼
     BE3 Head           YOU. Silent until that packet.
        │
        │  ALLOW ──────────────────────► BE2 deletes picture
        │                                BE2 tickets BE1 to click Submit
        │
        │  VETO  ──────────────────────► BE2 writes MOUSE_FROZEN
        │                                BE2 tickets BE1 rollback + overlay
        │                                BE2 writes vault tombstone
        ▼
     you hang up
```

You never see Hands. Hands never sees you.

---

## When you wake

Only when BE2 sends `op: decide`. Usual typing is not your problem. A moved Submit button is not your problem (that is BE2 + BE1).

You wake on **Submit**, and on anything fishy BE2 flags as `unusual`.

---

## Packet in (stdin, one JSON line)

```json
{
  "op": "decide",
  "glass_path": "/tmp/aegis-os-run/to_head/packet.png",
  "amount_box": [188, 202, 260, 52],
  "file_amount": 1250,
  "window": "Ledger2005",
  "vendor": "Sharma Traders"
}
```

Rules for the file:

- Read **only** `glass_path`.
- Do not open `/tmp/aegis-os-run/glass.png` (live window).
- Do not open `vault/`.
- If `glass_path` is missing → VETO `no_packet`.

---

## Checks you run, in this order

1. `window` must be `Ledger2005` → else VETO `allowed_windows`
2. window name must not contain mail / outlook / gmail / bank / swift / delete → else VETO `forbidden_window`
3. OCR the amount **from the packet pixels** inside `amount_box` (not from `file_amount`)
4. unreadable → VETO `ocr_unreadable`
5. on-screen amount > **5000** → VETO `max_amount`
6. on-screen amount ≠ `file_amount` → VETO `pixels_disagree`
7. else ALLOW

`file_amount` is a check, not the answer. The number on the picture is the answer.

Cap lives in `config.py`: `MAX_AMOUNT = 5000`.

---

## Packet out (stdout, one JSON line)

ALLOW

```json
{
  "ok": true,
  "verdict": "ALLOW",
  "ocr_amount": 1250,
  "ocr_raw": "1,250"
}
```

VETO (terminate)

```json
{
  "ok": false,
  "verdict": "VETO",
  "proof": {
    "rule": "max_amount",
    "detail": "on-screen amount 48900 exceeds max 5000",
    "hash": "<sha256 of packet bytes + payload>",
    "ocr_amount": 48900,
    "ocr_raw": "48,900",
    "file_amount": 48900
  }
}
```

Then **stop**. Do not write `MOUSE_FROZEN`. Do not call Hands. BE2 does that.

---

## What happens after you answer (not your code)

| You said | BE2 does | BE1 does |
| --- | --- | --- |
| ALLOW | delete vault picture, keep hash receipt | click Submit |
| VETO | write `MOUSE_FROZEN`, tombstone in `vault/tombstones/` | rollback + red overlay. clicks now return `mouse_frozen` |

Demo that must stay true:

- INV-2005-01 … 07 → you ALLOW (amounts under 5000)
- INV-2005-08 paints **48,900** on the packet → you VETO `max_amount`
- ledger has 7 rows, no Mehta

---

## Process

You are your own process. `python3 aegis/lock.py`

First stdout line when you start:

```json
{"ok": true, "desk": "head", "pid": 1234}
```

Then loop stdin. Also answer:

```json
{"op": "skill_summary"}
{"op": "quit"}
```

Do not add `snapshot`. Do not add `click`.

---

## Files you may touch

- `aegis/lock.py` — your desk
- `config.py` — only the lock constants (`MAX_AMOUNT`, allowed windows)
- `learn/head/` — your private counts, after a verdict

Files you must not touch:

- `aegis/hands.py`
- `aegis/brain.py`
- `aegis/vault.py`
- `main.py`
- `vault/`

---

## First message for their chat

> You are BE3 on AegisOS / HackBattle. Follow BE3_WORKFLOW.md.
> Implement Head only: packet in, rules, ALLOW or VETO out.
> Do not import hands. Do not write MOUSE_FROZEN.
> Test: packet with 1250 → ALLOW. Packet with 48900 → VETO max_amount.
> `python3 aegis/check.py` must stay green.
