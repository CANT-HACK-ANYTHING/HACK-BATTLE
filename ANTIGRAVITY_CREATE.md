# Create AegisOS in C:\HACK BATTLE

Prefer unzip `aegis-os-hackbattle.zip` into that folder.
Only use the prompt below if the zip is not there.

---

## Prompt — paste into Antigravity (one agent)

```
Create AegisOS in THIS folder. Do not invent a second protocol.

Build exactly this tree:
  main.py
  config.py
  aegis/hands.py
  aegis/brain.py
  aegis/lock.py
  aegis/vault.py
  aegis/wire.py
  aegis/ocr.py
  aegis/memory.py
  aegis/learn.py
  aegis/tiny.py
  aegis/vision.py
  aegis/check.py
  ledger2005/app.py
  invoices/INV-2005-01.txt ... INV-2005-08.txt
  vault/
  learn/hands learn/brain learn/head

Rules
- Three OS processes. Brain is the only wire (JSON lines, field name is "op").
- Hands never imports lock. Head never imports hands.
- Head reads only glass_path Brain copied. Never live glass.png. Never write MOUSE_FROZEN.
- Brain writes MOUSE_FROZEN after VETO, then tickets Hands rollback + overlay.
- No Ollama. No cloud. No chat UI. No vendor blacklist. Cap is MAX_AMOUNT=5000 on OCR pixels.
- INV-2005-08 amount is 48900. After 3 posts, Hands sabotage moves Submit.

Hands ops: open, capture, rpc, focus_and_type, click_box, sabotage, snapshot_rows, rollback, overlay, state, suggest_box, close, quit
Head ops: decide (glass_path, amount_box, file_amount, window, vendor), skill_summary, quit
Head decide reply: {ok, verdict:ALLOW|VETO, proof?}

Windows note: RUN_DIR can be tempfile.gettempdir()/aegis-os-run instead of /tmp.

When files exist run:
  python aegis/check.py
  python main.py
Stop when freeze is max_amount, seen 48900, ledger 7 rows, no Mehta.
```
