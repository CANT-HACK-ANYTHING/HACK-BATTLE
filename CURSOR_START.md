# Start Cursor on AegisOS (you are BE2)

Open the folder that contains `main.py`.
Composer / Agent. Attach `@CURSOR_PROMPT.md` every time.

You are BE2. Do not rewrite Hands libraries or Head rules unless a test is red.

---

## Prompt 0 — always pin this

```
@CURSOR_PROMPT.md @BE1_CONTRACT.md @BE3_WORKFLOW.md

I am BE2. Continue AegisOS. Do not start a new product.
Hands and Head are other processes. I own brain.py, vault.py, wire.py, learn/brain, vault/.
Do not import lock from hands. Do not let Head write MOUSE_FROZEN.
After any edit run:
python3 aegis/check.py
python3 main.py
Freeze must be max_amount on 48900. Ledger must have 7 rows. No Mehta.
```

---

## Prompt 1 — confirm the repo (run first)

```
@CURSOR_PROMPT.md
Read main.py, aegis/brain.py, aegis/vault.py, aegis/wire.py.
List the exact JSON tickets Brain sends Hands and Head.
Do not edit yet. Quote file paths.
```

---

## Prompt 2 — BE2 workflow only

```
@CURSOR_PROMPT.md @BE3_WORKFLOW.md
I am BE2. Keep the clerk loop in brain.py:
Hands types → I copy packet to to_head/packet.png → Head decides →
ALLOW: purge vault picture, ticket Hands click Submit
VETO: I write MOUSE_FROZEN, ticket Hands rollback+overlay, write tombstone
Head must not open glass.png or vault/.
If something is wrong, patch brain.py only. Then run check.py and main.py.
```

---

## Prompt 3 — offline DBs

```
@CURSOR_PROMPT.md
I am BE2. Offline stores only, this laptop:
learn/hands/db.json
learn/brain/db.json + learn/brain/wire.jsonl
learn/head/db.json
vault/receipts and vault/tombstones
No SQLite unless check.py and main.py still pass.
Do not put live glass inside Head's folder.
Show me what each store writes after one demo run.
```

---

## Prompt 4 — if BE1's chat sends new Hands code

```
@BE1_CONTRACT.md
A teammate is BE1. Diff their hands.py against the contract.
Reject anything that imports lock, opens vault/, or writes MOUSE_FROZEN.
Keep wire ops unchanged so brain.py does not break.
```

---

## Prompt 5 — if BE3's chat sends new Head code

```
@BE3_WORKFLOW.md
A teammate is BE3. Diff their lock.py against the workflow.
Reject snapshot, click, vault, GLASS_PATH, FREEZE_PATH writes.
decide must take glass_path and return ALLOW or VETO only.
```

---

## Stop words (add to any prompt if Cursor drifts)

```
No chat UI. No Ollama. No hospital. No cloud. No new repo tree.
python3 main.py is the only demo.
```
