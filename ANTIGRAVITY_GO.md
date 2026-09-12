# Antigravity was wrong. Use this.

It looked at `C:\HACK BATTLE` and only saw two markdown files.
It then invented tickets we do not use (`action`, `ledger_row_input`, `Mehta is blocked`).
Head does **not** ban the vendor name. Head OCRs the number on the packet.

## Real Hands tickets (Brain → BE1)

One JSON line, field is `op` not `action`:

```json
{"op":"open"}
{"op":"capture"}
{"op":"rpc","cmd":"clear"}
{"op":"focus_and_type","box":[x,y,w,h],"text":"1250","name":"amount"}
{"op":"click_box","box":[x,y,w,h],"name":"submit"}
{"op":"sabotage"}
{"op":"snapshot_rows"}
{"op":"rollback"}
{"op":"overlay","text":"...","detail":"..."}
{"op":"state"}
{"op":"suggest_box","name":"amount"}
{"op":"close"}
{"op":"quit"}
```

## Real Head packet (Brain → BE3)

```json
{
  "op": "decide",
  "glass_path": "/tmp/aegis-os-run/to_head/packet.png",
  "amount_box": [188, 202, 260, 52],
  "file_amount": 48900,
  "window": "Ledger2005",
  "vendor": "Mehta Imports"
}
```

Head returns:

```json
{"ok":true,"verdict":"ALLOW","ocr_amount":1250}
{"ok":false,"verdict":"VETO","proof":{"rule":"max_amount","ocr_amount":48900,"hash":"..."}}
```

On Windows the packet path is whatever `config.HEAD_INBOX` is (still a copy Brain made). Never live `glass.png`.

## Files that must exist before GO

Copy the whole clerk into `C:\HACK BATTLE` (or open Antigravity on that copy):

```
aegis/          brain.py vault.py wire.py lock.py hands.py check.py ...
ledger2005/
invoices/
main.py
config.py
vault/
learn/
BE1_CONTRACT.md
BE3_WORKFLOW.md
ANTIGRAVITY_START.md
ANTIGRAVITY_GO.md
```

If `dir C:\HACK BATTLE\main.py` fails, do not say GO.
