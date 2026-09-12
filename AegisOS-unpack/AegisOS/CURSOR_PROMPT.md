# AegisOS — Cursor / Antigravity prompt

Paste this as the system/task prompt. Do not start a new product.

---

You are continuing **AegisOS**, an offline clerk on one laptop. Not a platform. Not a chatbot. Not a cloud computer-use agent. Not a foundation model. Not Epic/SWIFT.

## One-liner
Local hands. Local memory. A lock that cannot click.

## What it does
Point it at `invoices/` and the Ledger2005 window. It types and clicks like a clerk. If Submit moves, Brain finds it again on the live glass. If the number on screen is illegal or disagrees with the file, Head freezes the mouse and shows why. Nothing leaves the machine.

## Three desks (never collapse these)
```
invoice + glass
        ↓
     [ Brain ]     ← only middle. Holds memory. Only wire.
      ↓       ↓
 [ Hands ]   [ Head ]
  click        silent until unusual
  type         ALLOW / VETO
```
- Hands and Head are **separate OS processes**. They must not import each other.
- Brain talks JSON-lines via `aegis/wire.py`.
- `main.py` is a launcher only. It must not post invoices.
- Usual work: Brain → Hands only.
- Unusual (Submit, bad window, on-screen amount): Brain → Head with a dossier. Hands stays out of that call.
- Head never moves the mouse. Hands never decides.

## Hard rules (do not soften)
- No network. No GPU. No new foundation model. No Tesseract. No Ollama. No hosted API.
- Head veto path: `config.py` + OCR of the **packet** Brain copied to `to_head/packet.png`. Never live `glass.png`. Never write `MOUSE_FROZEN`. Amount comes from pixels, not invoice JSON.
- Learning may suggest (`p_veto`, motor hints). Learning must not override `MAX_AMOUNT`.
- Do not add a chat window, copilot dock, hospital/bank slides, or cloud Operator UI.
- Do not present any other GitHub dump as the product.
- Fake app is `ledger2005/`. Real click on this machine’s glass is enough.

## Tree (keep this shape)
```
aegis/hands.py      # operator process
aegis/brain.py      # middle / only wire
aegis/lock.py       # head process
aegis/memory.py     # control graph + relocalize
aegis/ocr.py        # read amount off glass
aegis/learn.py      # three private stores + skills
aegis/tiny.py       # from-scratch logistic unit (CPU)
aegis/train.py      # replay stores into units
aegis/wire.py       # JSON-line process wire
config.py
ledger2005/app.py
invoices/INV-2005-01.txt … INV-2005-08.txt
main.py
learn/{hands,brain,head}/db.json
learn/{hands,brain,head}/model.json
```

## Commands that must keep working
```bash
python3 main.py          # full demo, wifi unused
python3 aegis/train.py   # replay events into the three units
```

Demo must still do exactly this:
1. Post INV-2005-01..03.
2. Move Submit. Memory/Brain rebinds. 04–07 still post.
3. INV-2005-08 paints 48,900. Head OCRs the glass, vetoes `max_amount`, overlay + hash, ledger has **no** Mehta row.

## AI that exists (do not replace with an LLM)
Each desk has its own store and a 1-neuron logistic unit trained by SGD in `aegis/tiny.py`.
- Hands: motor — which boxes accepted type/click.
- Brain: routes — field order, rebinds.
- Head: anomaly — z-score + `p_veto`. Advisory only.
Grow these from `learn/*/db.json`. Do not download weights. Do not call OpenAI/Gemini/Anthropic. Do not add pytesseract, torch, or Ollama. Glass is read by `aegis/ocr.py` (Pillow + DejaVu templates). The only third-party PyPI package is Pillow.

## If you add code
- Prefer small patches to existing files.
- New files only when a desk would otherwise import the other desk.
- Persist Brain’s wire log (`learn/brain/wire.jsonl`) if you touch logging; that log is the future NotebookLM-style scroll UI. **Do not build the chat UI.**
- After changes: run `python3 aegis/train.py` and `python3 main.py` and paste the last freeze block (rule, ocr, ledger row list).

## Done looks like
Same three-process demo, boringly reliable, plus the three units’ `steps` going up after train. If a slide needs hospital, banking, chatbot, or “first computer-use agent,” delete the slide.
