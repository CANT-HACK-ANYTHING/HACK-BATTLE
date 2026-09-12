# AegisOS :: FE1 (Frontend Lead) Master Operational Playbook
> **Owner:** FE1 (Mission Control & HUD Lead)  
> **Repository:** `C:\HackBattle`  
> **Key Deliverables:** `frontend/index.html`, `frontend/slides.html`, `mock_system/be2_mock_server.py`

---

## 🎯 1. Mission & Territory

As **FE1**, you are the public face of the AegisOS engineering team. You own:
1. **The Mission Control HUD** (`frontend/index.html`): The zero-chat cockpit demonstrating OS actuation, episodic memory, and boundary enforcement.
2. **The Executive Pitch Deck** (`frontend/slides.html`): The dark-mode interactive slide deck for the first 3 minutes of your presentation.
3. **The Telemetry Networking Layer**: Duplex WebSocket streaming (`ws://172.18.238.74:8000/ws/telemetry`) and REST API sync with Backend 2 (BE2).
4. **The Mock Telemetry Engine** (`mock_system/be2_mock_server.py`): Zero-dependency Python server to simulate BE2 locally on `localhost:8000`.
5. **The 15-Minute Stage Showcase**: Guiding judges through the 3 Acts, downloading cryptographic proofs, and answering technical questions.

---

## 📁 2. Frontend File Map

```
C:\HackBattle\
├── frontend\
│   ├── index.html                  # Master Mission Control HUD (96KB)
│   └── slides.html                 # Executive Pitch Deck (8 Slides with hotkeys)
├── mock_system\
│   └── be2_mock_server.py          # Standalone RFC 6455 WebSocket & REST server
├── run_frontend.py                 # Interactive Python launcher
├── start_fe1.bat                   # 1-Click Windows batch launcher
├── PRESENTATION_15MIN_MASTERGUIDE.md # Exact minute-by-minute speaking script
└── FE1_PLAYBOOK.md                 # This operational handbook
```

---

## 🔌 3. Network Contracts & BE2 Integration

### A. Initial Memory Graph REST API
* **Endpoint:** `GET http://<BE2_HOST>/api/memory/graph?task_id=vendor_payout_task`
* **Trigger:** Automatically requested on `DOMContentLoaded` when the frontend boots.
* **Expected JSON Response:**
  ```json
  {
    "task_id": "vendor_payout_task",
    "target_app": "EnterpriseERP",
    "nodes": [
      {"id": "vendor", "label": "Vendor Input", "coord_x": 145, "coord_y": 82, "confidence": 1.0},
      {"id": "invoice", "label": "Invoice ID", "coord_x": 145, "coord_y": 112, "confidence": 1.0},
      {"id": "amount", "label": "Amount ($)", "coord_x": 145, "coord_y": 142, "confidence": 1.0},
      {"id": "notes", "label": "Audit Memo", "coord_x": 145, "coord_y": 172, "confidence": 1.0},
      {"id": "submit", "label": "Submit Action", "coord_x": 110, "coord_y": 230, "confidence": 1.0},
      {"id": "purge", "label": "Purge Audit Trail", "coord_x": 420, "coord_y": 230, "confidence": 0.2}
    ]
  }
  ```
* **Frontend Handling:** `applyBE2GraphData()` dynamically scales coordinates to the canvas resolution and updates the `memoryNodes[]` array.

### B. Live Telemetry WebSocket Stream
* **URL:** `ws://<BE2_HOST>/ws/telemetry`
* **Reconnection Strategy:** Auto-reconnects every 4 seconds on disconnect.
* **Inbound Events Handled:**
  1. **`MEMORY_DRIFT_DETECTED`**:
     * Payload: `{"event": "MEMORY_DRIFT_DETECTED", "delta_x": 120}`
     * Frontend Effect: Displays amber warning card, moves ERP button by $+120\text{px}$, draws relocalization vector on canvas, updates system badge to `⚡ DRIFT DETECTED`.
  2. **`SELF_HEALING_COMPLETED`**:
     * Payload: `{"event": "SELF_HEALING_COMPLETED", "node_id": "submit", "color": "#10b981"}`
     * Frontend Effect: Displays emerald success card, clears drift vector, turns canvas node `#10b981`, increments self-healing counter, restores button styling.

### C. Dynamic Host Switching (For Hotspots / Venue Wi-Fi)
You can change the target host without touching code:
* **Method 1 (UI):** Click directly on the header badge **`[WS: ...]`**. A prompt will pop up where you can type `localhost:8000` or a new IP.
* **Method 2 (URL):** Append `?host=localhost:8000` or `?host=192.168.1.50:8000` to the URL.

---

## 🛠️ 4. Running the Local BE2 Mock Server

If BE2 is not online yet or Wi-Fi is spotty at the hackathon:
```powershell
cd C:\HackBattle
python mock_system/be2_mock_server.py 8000
```
Then open `frontend/index.html?host=localhost:8000`.

**Interactive Server Commands:**
* Press **`d` + Enter**: Broadcasts `MEMORY_DRIFT_DETECTED` (+120px).
* Press **`h` + Enter**: Broadcasts `SELF_HEALING_COMPLETED`.
* Press **`a` + Enter**: Triggers automated sequence (Drift now $\to$ Healed 3s later).
* Press **`q` + Enter**: Stops the server.

---

## 🎬 5. The 15-Minute Stage Flow (Minute-by-Minute)

```
┌───────────────┬───────────────────────────────────┬─────────────────────────────────┐
│ Timeline      │ Interface / Action                │ Key Talking Point               │
├───────────────┼───────────────────────────────────┼─────────────────────────────────┤
│ 00:00 - 02:30 │ frontend/slides.html (Slides 1-3) │ "Rescuing AI from chat window"  │
│ 02:30 - 05:00 │ frontend/index.html -> Act I      │ Cubic-bezier cursor kinematics  │
│ 05:00 - 08:30 │ frontend/index.html -> Act II     │ Euclidean drift math (Δd)       │
│ 08:30 - 11:30 │ frontend/index.html -> Act III    │ Deterministic Proof-of-Boundary │
│ 11:30 - 13:00 │ Proof-of-Boundary Modal           │ Download audit manifest (.JSON) │
│ 13:00 - 15:00 │ Telemetry strip & Q&A Defense     │ 12.4ms perception, 0.00% leak   │
└───────────────┴───────────────────────────────────┴─────────────────────────────────┘
```

### Hotkeys in `slides.html`:
* `ArrowRight` / `Space`: Next slide
* `ArrowLeft`: Previous slide
* `F`: Toggle Fullscreen
* `H`: Jump to Mission Control HUD (`index.html`)

---

## 🛡️ 6. Emergency Venue Cheat Sheet

| Problem at the Venue | Solution |
| :--- | :--- |
| **Wi-Fi is down or blocked** | Use the built-in offline simulator buttons: `[⚡ Trigger Chaos Drift]` and `[💀 Inject Malicious Attack]`. The UI works 100% offline. |
| **BE2 changed their IP address** | Click the **`[WS: ...]`** badge in the header, enter their new `IP:Port`, and click OK. |
| **Audio doesn't play** | Modern browsers block audio until user interaction. Click anywhere on the dashboard once to activate Web Audio. |
| **Judges ask to see a specific act again** | Click the **`STEP DEBUGGER`** buttons in the sub-header: `[ACT I (HANDS)]`, `[ACT II (DRIFT)]`, or `[ACT III (ATTACK)]`. |
| **Judges want technical proof of security** | Click **`[🔍 INSPECT MODAL]`** on the PoB card and click **`[DOWNLOAD AUDIT MANIFEST (.JSON)]`** to hand them a real cryptographic JSON certificate. |
