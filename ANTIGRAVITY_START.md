# AegisOS on Google Antigravity — from scratch

Use **one agent**. Do not open Manager / multi-agent. If Antigravity offers “Hands agent + Head agent + UI agent”, refuse.

Open the folder that contains `main.py`.

---

## Prompt 0 — paste first (pin every turn)

```
You are continuing AegisOS. One product. One laptop. Offline clerk.

I am BE2. You work only on Brain / Wayne / wire / vault / offline DBs.

Do not start a new repo. Do not add a chat UI. Do not add Ollama. Do not add a foundation model.
Do not use a downloaded computer-use agent.

Desks:
- BE1 Hands = other process. click/type/screenshot. Never imports Head.
- BE2 Brain = me. Only wire. Owns vault/.
- BE3 Head = other process. Packet in, ALLOW or VETO out. Never writes MOUSE_FROZEN. Never opens live glass.png.

Read if present: CURSOR_PROMPT.md, BE1_CONTRACT.md, BE3_WORKFLOW.md, main.py, aegis/brain.py, aegis/vault.py, aegis/wire.py, aegis/lock.py.

After any edit run:
python3 aegis/check.py
python3 main.py
Must end: rule max_amount, OCR 48,900, 7 ledger rows, no Mehta.

If check or demo fails, fix brain.py / vault.py / wire.py first. Do not rewrite hands.py or lock.py unless a test proves they are broken.

Stop after the first read. Wait for my next prompt.
```

---

## Prompt 1 — map only

```
List the JSON tickets Brain sends Hands and Head. Quote file paths. No edits.
```

---

## Prompt 2 — workflow

```
Keep this loop in brain.py only:
Hands types → I copy vault picture to to_head/packet.png → Head decide →
ALLOW: purge picture, ticket Hands click Submit
VETO: I write MOUSE_FROZEN, ticket Hands rollback+overlay, tombstone
Then run check.py and main.py. Paste the freeze block.
```

---

## Prompt CLEAN — only if this folder is a dirty GitHub clone

```
Show git status and top-level files. List deletes first.
Delete only: node_modules, from scratch/, imagine_images/, __pycache__, hospital/bank slides, duplicate product trees.
Keep: aegis/ ledger2005/ invoices/ vault/ learn/ main.py config.py README.md requirements.txt BE*.md *START.md CURSOR_PROMPT.md
No force-push. No commit until I say commit.
```

---

## If Antigravity tries to spawn extra agents

```
Single agent. BE2 only. No frontend agent. No Head agent. No Hands agent.
```
