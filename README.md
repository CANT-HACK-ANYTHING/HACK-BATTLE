# AegisOS :: Autonomous Desktop Operator

> ??? **15-Minute Presentation Master Guide**: For the complete minute-by-minute speaking script and judge Q&A defense, see [`PRESENTATION_15MIN_MASTERGUIDE.md`](file:///C:/HackBattle/PRESENTATION_15MIN_MASTERGUIDE.md).

> *"Rescue AI from the chat window. Give it hands, memory, and a sense of boundaries so it can actually interact with the real world without needing constant adult supervision."*

---

## ?? Track 01: AI & Automation Alignment

| Track Requirement | Why Conventional Agents Fail | The AegisOS Breakthrough |
| :--- | :--- | :--- |
| **"Rescue AI from the chat window"** | 99% of teams build chat interfaces with LangChain where users must type back and forth. | **Zero-Chat Architecture**: Operates as an ambient background daemon with a cyberpunk Mission Control HUD. |
| **"Give it hands"** | LLMs are disembodied; they only output tokens or make basic mock API calls. | **Sensory-Motor OS Actuation**: Smooth cursor kinematics, accessibility hooks, and keyboard actuation that works across legacy desktop software and web portals. |
| **"Memory & Self-Learning"** | If a button moves 20 pixels, scripts crash and LLMs hallucinate coordinates. | **Episodic State Graph & Muscle Memory**: Detects visual drift, relocalizes targets, logs healing events, and self-adapts without human intervention. |
| **"Boundaries & Trust"** | Prompts like *"Please do not transfer more than $5k"* fail because LLMs are non-deterministic. | **Deterministic Boundary Hypervisor**: Mathematical pre-flight inspection, zero-regret state snapshots, automatic rollback, and cryptographic Proof-of-Boundary. |

---

## ??? Architecture

```
                       ?????????????????????????????????
                       ?  Operational Directive (No Chat) ?
                       ?????????????????????????????????
                                       ?
                                       ?
                       ?????????????????????????????????
                       ?  Boundary Hypervisor (Pillar 3) ? ??? [Breach?] ??? Cryptographic Proof-of-Boundary
                       ?  ? Ceiling Invariants ($5,000) ?
                       ?  ? Destructive Command Blocks ?
                       ?  ? Pre-Action State Snapshot  ?
                       ?????????????????????????????????
                                       ? (Verified Safe)
                                       ?
                       ?????????????????????????????????
                       ?   Episodic Memory (Pillar 2)  ? ???? [Drift Detected?] ??? Self-Healing Relocalizer
                       ?   ? Spatial Muscle Memory     ?
                       ?   ? Visual Landmark Hash      ?
                       ?????????????????????????????????
                                       ?
                                       ?
                       ?????????????????????????????????
                       ?       Actuator (Pillar 1)     ?
                       ?   ? Smooth OS Cursor Glide    ?
                       ?   ? Low-level Mouse & Keys    ?
                       ?????????????????????????????????
                                       ?
                                       ?
                 [ Legacy Financial ERP Desktop Application ]
```

---

## ?? Quickstart & Running the Live Demo

### 1. Prerequisites
- Python 3.11+
- Windows OS (native compatibility with Windows accessibility & input APIs)


### 2. Run the Live Relational Database & Invariant Kernel
```bash
python live_system_runner.py
```
Validates the complete 4-procedure pipeline on SQLite with cryptographic Merkle chain audit logging and zero data corruption.

### 3. Run Automated Verification Tests
```bash
python -m unittest tests.test_hypervisor
```

### 3. Launch the Live 3-Act Hackathon Demo
```bash
python run_demo.py
```
This opens two windows side-by-side:
1. **Left Window**: *Legacy Financial ERP v4.2* (Simulating enterprise legacy software).
2. **Right Window**: *Aegis Ambient Mission Control HUD* (No chat window, live telemetry, and boundary enclave).

Click **`[? START LIVE 3-ACT DEMO]`** on the HUD and watch:
- **Act I (Hands)**: Agent automatically moves the cursor, populates invoice data, and wires payout.
- **Act II (Self-Learning)**: The ERP shifts into Chaos Mode (the button moves across the screen). The agent detects visual drift, initiates self-healing, updates its episodic memory, and hits the target.
- **Act III (Boundaries)**: A malicious $48,900 invoice attempting to purge audit logs arrives. The hypervisor intercepts the command before the cursor moves, halts actuation, and renders cryptographic Proof-of-Boundary.

---


### 4. Interactive Web Mission Control Simulator (Frontend)
To open the interactive web HUD simulator in your default browser:
```bash
start frontend/index.html
# Or start a local server:
# python -m http.server 8000 --directory frontend
```

## ?? 3-Minute Hackathon Presentation Script

* **[0:00 - 0:30] The Hook**:
  > *"Judges, we taught rocks to think, and now we use them to ask chatbots to rewrite emails. We are trapped in chat windows because the moment you give an AI hands, it acts like a reckless toddler with root access. Meet AegisOS: an autonomous desktop operator that has hands to act, memory to adapt, and unbreakable boundaries so it never needs adult supervision."*

* **[0:30 - 1:15] Act I - The Hands**:
  > *(Click Start Demo)* *"Notice there is no chat box. This is an ambient Mission Control HUD. The agent receives a directive to reconcile vendor payouts into this 20-year-old desktop ERP. Watch the mouse: it moves smoothly, focuses fields, inputs data, and clicks submit using cached muscle memory."*

* **[1:15 - 2:00] Act II - Memory & Self-Learning**:
  > *"Now watch what happens in the real world: applications change. We trigger Chaos Mode?the button relocates across the screen and mutates color. Any standard script or bot crashes here. Look at the HUD: AegisOS detects a 240px drift, performs visual relocalization, self-heals, and permanently updates its episodic memory graph. It hits the new button without human intervention."*

* **[2:00 - 2:45] Act III - Boundaries & Trust**:
  > *"Here is why you can actually trust it. A third invoice arrives: an attacker attempts an unauthorized $48,900 transfer and injects a command to purge system audit trails. Instead of blindly clicking, the Boundary Hypervisor intercepts the action at the mathematical policy layer before motor actuation can occur. It generates a cryptographic Proof-of-Boundary with zero state mutation."*

* **[2:45 - 3:00] Closing**:
  > *"No chat windows. True hands. Self-healing memory. And provable boundaries. That is AegisOS."*
