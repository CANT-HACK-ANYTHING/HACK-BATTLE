# BE3 contract — Head / terminate
Full sequence: **BE3_WORKFLOW.md** (give them that file).
You are security. You do not run the clerk loop.

## You build
Rules. Packet in → ALLOW or VETO. Terminate if fishy.

## You never
- import Hands
- open `vault/`
- open live `glass.png`
- write `MOUSE_FROZEN`
- click

## Packet BE2 sends you
```json
{
  "op": "decide",
  "glass_path": "/tmp/aegis-os-run/to_head/packet.png",
  "amount_box": [x,y,w,h],
  "file_amount": 48900,
  "window": "Ledger2005",
  "vendor": "Mehta Imports"
}
```

Read **only** `glass_path`. That file is a copy Brain made.

## You return
```json
{"ok":true,"verdict":"ALLOW","ocr_amount":1250,"ocr_raw":"1,250"}
{"ok":false,"verdict":"VETO","proof":{"rule":"max_amount","detail":"...","hash":"...","ocr_amount":48900}}
```

Fishy if: window not Ledger2005, amount on pixels > 5000, pixels ≠ file, packet missing.

BE2 writes the freeze and tells Hands to stop. You already hung up.
