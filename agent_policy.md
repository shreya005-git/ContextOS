# ContextOS - Agent Policy

## 1. Purpose

ContextOS is an agentic operational trust layer that continuously evaluates whether a high-value operation still deserves to proceed.

It does not treat any single network signal as truth.

Instead, it reasons across multiple independent signals and identifies inconsistencies between the expected operational context and the observed context.

The core principle is:

> **The agent determines what evidence it needs. The Context Evaluator determines what the evidence permits.**

---

## 2. Demo Operation

ContextOS will demonstrate a field technician performing a high-value network equipment replacement at an authorized facility.

### Expected Context

* **Technician:** Alex
* **Operation:** Network equipment replacement
* **Location:** Facility A
* **Risk:** HIGH
* **Authorized Device:** Test device

The operation remains subject to continuous reassessment after it begins.

---

## 3. Available Network Evidence

ContextOS currently has access to three Nokia Network as Code / CAMARA capabilities.

### 3.1 Location Verification

**Question:**

> Is the device within the authorized operational area?

**Current evidence:**

* `TRUE`
* `FALSE`

ContextOS treats this as evidence about physical context, not proof of identity or legitimacy.

---

### 3.2 Device Connectivity

**Question:**

> What is the device's current network connectivity status?

**Example response:**

* `CONNECTED_SMS`

The raw Nokia response must be preserved.

ContextOS should interpret the result only in relation to the operation's expected context.

---

### 3.3 SIM Swap

**Question:**

> Does the SIM Swap capability report a detected SIM change?

**Current evidence:**

* `swapped = TRUE`
* `swapped = FALSE`

The raw API response must be preserved.

ContextOS must not claim a precise time or duration for the SIM change unless the API actually provides that information.

A positive SIM Swap signal is treated as an **identity-context anomaly**, not automatic proof of fraud.

---

## 4. Agentic Evidence Selection

The agent must NOT automatically call every available API.

Its primary responsibility is to determine:

> **What evidence is necessary to establish sufficient operational trust for this specific operation?**

The agent considers:

* Operation type
* Operation risk
* Expected operational context
* Evidence already collected
* Newly observed changes
* Conflicts between signals
* Whether the existing evidence is sufficient

### Principle

Different operations may require different evidence.

For example:

A lower-risk operation may initially require only location evidence.

A high-risk operation may require both physical-context and identity-context evidence.

The agent should therefore request the **minimum sufficient evidence**, rather than blindly calling every available capability.

---

## 5. Agent Output

The agent does NOT make the final authorization decision.

Instead, it produces an evidence plan.

Example:

```json
{
  "evidence_plan": [
    "LOCATION",
    "SIM_CONTEXT"
  ],
  "reason": "This is a high-risk operation requiring physical and identity-context evidence."
}
```

The agent may request additional evidence when the currently available evidence is insufficient or inconsistent.

The agent must not invent evidence.

---

## 6. Context Evaluation

After the requested evidence is collected, ContextOS passes the structured evidence to the Context Evaluator.

The Context Evaluator compares:

* Expected context
* Observed network evidence
* Operation risk
* Signal conflicts
* Previously observed context

The evaluator produces the operational decision.

The LLM cannot override this decision.

---

## 7. Operational Decisions

### ALLOW

The available evidence is sufficiently consistent with the expected operational context for the operation's risk level.

The operation may proceed.

### STEP-UP

The evidence contains an anomaly or is insufficient to establish sufficient trust.

Additional verification is required.

### HOLD

The evidence strongly conflicts with the expected operational context.

The operation should temporarily stop pending investigation.

---

## 8. Decision Principles

ContextOS must NOT use simplistic rules such as:

> "Two out of three signals are positive, therefore ALLOW."

Signals have different meanings depending on the operation and context.

### Example

**Operation:**

High-risk equipment replacement

**Evidence:**

* Location Verification → `TRUE`
* Device Connectivity → `CONNECTED_SMS`
* SIM Swap → `TRUE`

**Interpretation:**

Physical context is consistent, but an identity-context anomaly has been detected.

**Decision:**

`STEP-UP`

**Reason:**

> Physical context is consistent, but the identity context contains an anomaly. Because this is a high-risk operation, additional verification is required.

---

## 9. Continuous Reassessment

Authorization is not permanent.

ContextOS continuously monitors whether the operational context remains consistent.

### Example Timeline

#### 14:00 — Operation begins

* Location → `TRUE`
* Connectivity → `CONNECTED`
* SIM context → no detected anomaly

**Decision → ALLOW**

---

#### 14:37 — Context changes

* Location → `TRUE`
* Connectivity → `CONNECTED`
* SIM Swap signal → `TRUE`

**Decision → STEP-UP**

The system explains what changed and requests additional verification.

---

#### 15:02 — Physical context changes

* Location → `FALSE`
* Connectivity → `CONNECTED`
* SIM Swap signal → `TRUE`

**Decision → HOLD**

The operation is suspended because the observed physical context conflicts with the expected operational context.

---

## 10. Evidence Is Not Truth

CAMARA capabilities provide network evidence.

They do not independently prove that a person is legitimate, authorized, or acting correctly.

ContextOS therefore must never claim:

> "The technician is definitely legitimate."

Instead, it should communicate:

> **"The available evidence is consistent or inconsistent with the expected operational context."**

This distinction is fundamental to the system.

---

## 11. LLM Responsibilities

The LLM is responsible for:

* Understanding the operation
* Assessing what evidence is relevant
* Selecting the appropriate evidence tools
* Requesting additional evidence when necessary
* Interpreting evidence in context
* Identifying potential inconsistencies
* Explaining the Context Evaluator's decision
* Supporting continuous reassessment

The LLM is NOT responsible for:

* Overriding the Context Evaluator
* Inventing evidence
* Changing security policy
* Directly authorizing an operation
* Treating one signal as absolute truth
* Fabricating numerical confidence scores

---

## 12. Structured Evidence

All network responses should be normalized into structured evidence while preserving the original API result.

Example:

```json
{
  "signal": "LOCATION",
  "result": "MATCH",
  "raw_value": "TRUE",
  "source": "CAMARA_LOCATION_VERIFICATION",
  "observed_at": "..."
}
```

```json
{
  "signal": "CONNECTIVITY",
  "result": "CONNECTED_SMS",
  "raw_value": "CONNECTED_SMS",
  "source": "CAMARA_DEVICE_STATUS"
}
```

```json
{
  "signal": "SIM_CONTEXT",
  "result": "CHANGE_DETECTED",
  "raw_value": true,
  "source": "CAMARA_SIM_SWAP"
}
```

ContextOS must never add information that was not actually returned by the underlying API.

---

## 13. Core Agent Objective

The agent's objective is:

> **Determine what evidence is necessary to establish operational trust, gather that evidence through network capabilities, identify inconsistencies between expected and observed context, and continuously reassess whether the operation should proceed.**

The system's central distinction is:

> **Agent: What do I need to know?**

> **Network: What does the network observe?**

> **Context Evaluator: What does that evidence permit?**

> **UI: Why did the system make this decision?**
