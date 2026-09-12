# ContextOS

> **AI-powered operational trust using telecom network intelligence.**

ContextOS is an AI-driven operational trust system for high-risk field operations.

It continuously evaluates whether the current network context still supports an operation by combining:

* **AI evidence planning** using Gemini
* **LangGraph** workflow orchestration
* **CAMARA network APIs** through Nokia Network-as-Code
* **Deterministic trust evaluation**
* **Continuous reassessment**

The core principle is:

> **AI plans · Network observes · Trust Engine decides**

---

## The Problem

Authorization for high-risk operations is often treated as a snapshot.

A technician may be authorized to perform an operation based on a known location, device, and identity context at the beginning of the operation. But those conditions can change while the operation is still in progress.

ContextOS addresses this gap by continuously evaluating operational context.

Instead of asking only:

> "Was this operation authorized?"

ContextOS asks:

> **"Does the current operational context still support this operation?"**

---

## How ContextOS Works

ContextOS evaluates an operation through four stages:

### 1. Expected Context

The operation defines the expected conditions.

Example:

* Operation: Network equipment replacement
* Risk: HIGH
* Technician: Alex
* Expected location: Facility A
* Authorized device: Test device

### 2. AI Evidence Planning

The ContextOS AI agent uses **Gemini** to determine which network evidence is relevant to the current operational context.

Available capabilities include:

* Location Verification
* Device Status
* SIM Swap

The agent considers previously collected evidence during reassessment and can request fresh evidence when it can materially improve the evaluation.

The agent does **not** make the authorization decision.

### 3. Network Evidence

ContextOS invokes CAMARA capabilities through **Nokia Network-as-Code**.

The current implementation uses:

| Capability            | Operational purpose                                                      |
| --------------------- | ------------------------------------------------------------------------ |
| Location Verification | Verify whether the device is within the expected operational area        |
| Device Status         | Check the device's current network connectivity                          |
| SIM Swap              | Identify a SIM-change signal that may affect identity-context assessment |

Raw API responses are preserved where available rather than inventing additional information.

### 4. Trust Decision

The collected evidence is evaluated by a deterministic Trust Engine.

The final outcome is one of:

* **ALLOW** — available evidence supports the operation
* **STEP-UP** — additional verification is required
* **HOLD** — a critical context condition is inconsistent

The LLM cannot override the Trust Engine.

---

## Continuous Reassessment

Continuous reassessment is a core part of ContextOS.

When an operation is reassessed:

1. Previously collected evidence is retained.
2. Evidence freshness is considered.
3. Gemini determines whether additional evidence would materially improve the assessment.
4. Selected CAMARA capabilities are queried again.
5. New evidence is merged with the existing operational context.
6. The deterministic Trust Engine reevaluates the complete evidence set.

The agent can therefore:

* request a new capability,
* refresh previously collected evidence, or
* determine that existing evidence remains sufficient.

The current prototype triggers reassessment manually through the UI.

---

## Architecture

```text
┌──────────────────┐
│   React / Vite   │
│   ContextOS UI   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     FastAPI      │
│   Backend API    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    LangGraph     │
│ Agent Workflow   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│      Gemini      │
│ Evidence Planning│
└────────┬─────────┘
         │
         ▼
┌────────────────────────────┐
│ Nokia Network-as-Code      │
│        CAMARA APIs         │
│                            │
│ Location · Device · SIM    │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│     Deterministic          │
│       Trust Engine         │
│                            │
│ ALLOW · STEP-UP · HOLD     │
└────────────┬───────────────┘
             │
             ▼
        ContextOS UI
```

---

## AI Agent Design

ContextOS uses:

### Gemini

Used for:

* Evidence planning
* Context-aware evidence selection
* Reassessment planning

Gemini receives the operation context, previously collected evidence, and available network capabilities.

It returns an evidence plan and reasoning.

### LangGraph

Used to orchestrate the agent workflow.

Initial assessment:

```text
Plan Evidence
      ↓
Collect Evidence
      ↓
Evaluate Decision
```

Reassessment:

```text
Review Existing Context
      ↓
Plan Additional Evidence
      ↓
Collect Fresh Evidence
      ↓
Merge With Previous Evidence
      ↓
Deterministic Re-evaluation
```

---

## Deterministic Trust Engine

The Trust Engine is deliberately separated from the AI agent.

This ensures that the LLM is responsible for **planning evidence**, while deterministic policy is responsible for the final operational decision.

Examples of deterministic evaluation include:

* Location mismatch → **HOLD**
* High-risk operation with unavailable critical context → **STEP-UP**
* SIM-change anomaly → **STEP-UP**
* Unsupported/disconnected device state → **STEP-UP**
* Sufficient consistent evidence → **ALLOW**

This separation prevents the AI model from directly authorizing a high-risk operation.

---

## CAMARA / Nokia Network-as-Code Integration

ContextOS integrates with Nokia Network-as-Code using the Network-as-Code SDK.

The current implementation invokes:

* `Location Verification`
* `Device Status`
* `SIM Swap`

The backend preserves the source of each signal so that the UI can distinguish network evidence from the final Trust Engine decision.

Example evidence sources include:

```text
CAMARA_LOCATION_VERIFICATION
CAMARA_DEVICE_STATUS
CAMARA_SIM_SWAP
```

---

## Important Evidence Caveat

Network evidence is **contextual evidence, not absolute truth**.

For example, a SIM-swap signal is treated as an identity-context anomaly. It does not independently prove fraud or malicious activity.

Likewise, network location evidence does not independently prove that a particular human is physically holding a device.

ContextOS therefore uses network signals as evidence within a broader operational decision rather than claiming that they establish identity or intent by themselves.

---

## Project Structure

### Backend

```text
ContextOS/
├── src/
│   ├── agent.py
│   ├── api.py
│   ├── tools.py
│   └── trust_engine.py
├── .env
└── ...
```

### Frontend

```text
ContextOS-Frontend/
└── project/
    ├── src/
    │   ├── components/
    │   ├── services/
    │   ├── types/
    │   ├── App.tsx
    │   └── index.css
    ├── package.json
    └── vite.config.ts
```

---

## Running Locally

### Prerequisites

* Python
* Node.js and npm
* Nokia Network-as-Code API access
* Gemini API access

### Backend

From the backend root:

```powershell
cd "C:\Users\sachi\Documents\Projects\ContextOS"
uvicorn src.api:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Available endpoints:

```text
GET  /health
GET  /operation
POST /reassess
POST /reset
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Environment Variables

Create a `.env` file in the backend root:

```text
NAC_API_KEY=your_nokia_network_as_code_key
GEMINI_API_KEY=your_gemini_api_key
```

These credentials are required for the Nokia Network-as-Code and Gemini integrations.

**Never commit API keys or other secrets to the repository.**

### Frontend

From the frontend project directory:

```powershell
cd "C:\Users\sachi\Documents\Projects\ContextOS-Frontend\project"
npm install
npm run dev
```

The Vite development server runs at:

```text
http://localhost:5173
```

The frontend communicates with the FastAPI backend through the `/contextos-api` proxy.

---

## Demo Flow

The intended demo flow is:

```text
Operation
    ↓
Initial Assessment
    ↓
AI Evidence Plan
    ↓
CAMARA Network Evidence
    ↓
Trust Engine Decision
    ↓
Reassessment
    ↓
Fresh / Additional Evidence
    ↓
Trust Engine Re-evaluation
```

The UI exposes:

* Expected operational context
* Current Trust Engine decision
* Network evidence
* AI evidence plan
* Reassessment updates
* Evidence selected during reassessment

---

## Developer / Sandbox Environment

ContextOS was developed using the Nokia Network-as-Code developer environment and its available CAMARA API capabilities.

The integration uses real hosted API interfaces through Nokia Network-as-Code. The prototype environment should **not** be interpreted as production operator telemetry from a real technician or facility.

The network responses available to the prototype are therefore treated as network evidence for demonstrating the orchestration and decision architecture rather than as proof of production deployment.

---

## Current Prototype Scope

ContextOS currently demonstrates:

* AI-driven evidence planning
* Multi-CAMARA API orchestration
* Gemini + LangGraph agent workflow
* Nokia Network-as-Code integration
* Deterministic operational trust evaluation
* Continuous reassessment
* Previous evidence retention
* Evidence freshness awareness
* React/Vite frontend
* FastAPI backend
* End-to-end deployed prototype

The prototype intentionally does not claim to provide:

* definitive human identity verification
* proof of physical possession of a device
* fraud determination
* production operator telemetry
* autonomous authorization by an LLM

---

## Core Principle

> **AI PLANS · NETWORK OBSERVES · TRUST ENGINE DECIDES**

ContextOS turns network evidence into continuously evaluated operational context — so authorization can respond when the context changes.
