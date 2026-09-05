# ============================================================
# CONTEXTOS AI AGENT
#
# Gemini       -> evidence planning / reasoning
# LangGraph    -> agent orchestration
# Nokia NaaS   -> network evidence
# Trust Engine -> deterministic final decision
#
# IMPORTANT:
# Gemini NEVER authorizes the operation.
# The Trust Engine makes the final ALLOW / STEP-UP / HOLD decision.
# ============================================================

import json
from typing import TypedDict, Dict, Any

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.tools import (
    verify_location,
    check_connectivity,
    check_sim_swap,
)

from src.trust_engine import evaluate_operation

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GEMINI
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0,
)


# ============================================================
# DEMO OPERATION
# ============================================================

def build_operation():

    return {
        "id": "OP-CTX-0427",
        "name": "Network equipment replacement",
        "risk": "HIGH",
        "technician": "Alex",
        "expected_location": "Facility A",
        "authorized_device": "Test device",
    }

# ============================================================
# LANGGRAPH STATE
# ============================================================

class ContextState(TypedDict, total=False):

    operation: Dict[str, Any]

    evidence_plan: list
    agent_reasoning: str

    initial_evidence_plan: list
    initial_agent_reasoning: str

    evidence: Dict[str, Any]

    decision: Dict[str, Any]

    previous_evidence: Dict[str, Any]

    planning_fallback: bool

    evidence_failures: list

# ============================================================
# SUPPORTED CONTEXTOS CAPABILITIES
# ============================================================

SUPPORTED_TOOLS = [
    "LOCATION",
    "DEVICE_STATUS",
    "SIM_CONTEXT",
]


# ============================================================
# DETERMINISTIC FALLBACK POLICY
# ============================================================

def fallback_evidence_plan(
    operation,
    previous_evidence=None,
):

    previous_evidence = previous_evidence or {}

    # --------------------------------------------------------
    # INITIAL ASSESSMENT
    # --------------------------------------------------------

    if not previous_evidence:

        if operation.get("risk") == "HIGH":

            return {
                "evidence_plan": [
                    "LOCATION",
                    "SIM_CONTEXT",
                ],
                "reason": (
                    "Gemini planning was unavailable. "
                    "ContextOS applied its deterministic "
                    "minimum-sufficient evidence policy "
                    "for a high-risk operation."
                ),
            }

        return {
            "evidence_plan": [
                "LOCATION",
            ],
            "reason": (
                "Gemini planning was unavailable. "
                "ContextOS applied its deterministic "
                "fallback evidence policy."
            ),
        }

    # --------------------------------------------------------
    # REASSESSMENT
    #
    # Preserve the existing context and refresh the
    # available signals so the Trust Engine can evaluate
    # the complete operational context.
    # --------------------------------------------------------

    return {
        "evidence_plan": [
            "LOCATION",
            "DEVICE_STATUS",
            "SIM_CONTEXT",
        ],
        "reason": (
            "Gemini reassessment planning was unavailable. "
            "ContextOS requested fresh physical, connectivity, "
            "and identity-context evidence using its "
            "deterministic fallback policy."
        ),
    }


# ============================================================
# SAFE GEMINI RESPONSE EXTRACTION
# ============================================================

def extract_response_text(response):

    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, str):

                parts.append(item)

            elif isinstance(item, dict):

                if "text" in item:
                    parts.append(str(item["text"]))

                elif "content" in item:
                    parts.append(str(item["content"]))

        return " ".join(parts).strip()

    return str(content).strip()


# ============================================================
# PARSE GEMINI EVIDENCE PLAN
# ============================================================

def parse_evidence_plan(text):

    upper = text.upper()

    selected = []

    for tool in SUPPORTED_TOOLS:

        if tool in upper:
            selected.append(tool)

    # An empty plan is valid during reassessment when
    # Gemini determines that no additional evidence is needed.
    if not selected:
        return []

    # Always keep predictable ordering.
    return [
        tool
        for tool in SUPPORTED_TOOLS
        if tool in selected
    ]


# ============================================================
# EXTRACT REASONING
# ============================================================

def extract_reason(text):

    if "REASON:" in text:

        return text.split(
            "REASON:",
            1
        )[1].strip()

    return text.strip()

def build_plan_reason(tools, reassessment=False):

    if not tools:
        return (
            "Existing evidence remains sufficient for the "
            "current operational-context assessment."
        )

    descriptions = {
        "LOCATION": (
            "verify that the device is within the expected "
            "operational area"
        ),
        "DEVICE_STATUS": (
            "verify the device's current network connectivity state"
        ),
        "SIM_CONTEXT": (
            "check for a SIM change that could affect "
            "identity-context assessment"
        ),
    }

    selected = [
        descriptions[tool]
        for tool in tools
        if tool in descriptions
    ]

    if len(selected) == 1:
        evidence_text = selected[0]

    elif len(selected) == 2:
        evidence_text = (
            f"{selected[0]} and {selected[1]}"
        )

    else:
        evidence_text = (
            ", ".join(selected[:-1])
            + f", and {selected[-1]}"
        )

    if reassessment:
        return (
            "Fresh network evidence is being requested to "
            + evidence_text
            + "."
        )

    return (
        "Fresh network evidence is required to "
        + evidence_text
        + "."
    )


# ============================================================
# NODE 1 — GEMINI EVIDENCE PLANNING
# ============================================================

def plan_evidence(state: ContextState):

    operation = state["operation"]

    previous_evidence = state.get(
        "previous_evidence",
        {},
    )

    print(
        "\n=== GEMINI EVIDENCE PLANNING ==="
    )

    prompt = f"""
You are the ContextOS AI evidence-planning agent.

Your responsibility is to determine WHAT NETWORK EVIDENCE
is necessary to evaluate an operational context.

You DO NOT make the final authorization decision.

The deterministic Trust Engine makes the final:
ALLOW / STEP-UP / HOLD decision.

OPERATION:

{json.dumps(operation, indent=2)}

PREVIOUS EVIDENCE:

{json.dumps(previous_evidence, indent=2)}

AVAILABLE NETWORK CAPABILITIES:

1. LOCATION
Determines whether the device is inside the authorized
operational area.

2. DEVICE_STATUS
Returns the device's current network connectivity status.
The raw response may be values such as CONNECTED_SMS.

3. SIM_CONTEXT
Reports whether a SIM change was detected.

RULES:

1. Select ONLY supported capabilities.

2. Do not invent evidence.

3. Do not make ALLOW / STEP-UP / HOLD decisions.

4. Consider what is already known.

5. Request additional evidence when it helps resolve
   uncertainty or an observed anomaly.

6. Previously collected evidence remains available,
   but it may be stale.

7. During reassessment, you may request a previously
   collected capability when its CURRENT state is
   relevant to reassessing the operation.

8. Do not request a capability merely because it exists.
   Select it only when fresh evidence can materially
   improve the operational-context evaluation.

9. If the existing evidence remains sufficient and no
   fresh signal would materially improve the assessment,
   return an empty TOOLS list.

10. A SIM swap is an identity-context anomaly,
    not automatic proof of fraud.

11. Network evidence must be interpreted in operational context.

Return:

TOOLS: <comma-separated tools>

REASON: <brief explanation>
"""

    try:

        response = llm.invoke(prompt)

        text = extract_response_text(response)

        if not text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        tools = parse_evidence_plan(text)

        # ====================================================
        # POLICY GUARDRAIL
        #
        # For the initial HIGH-risk operation, ContextOS
        # requires physical + identity context regardless
        # of whether Gemini accidentally omits one.
        # ====================================================

        if (
            not previous_evidence
            and operation.get("risk") == "HIGH"
        ):

            tools = [
                "LOCATION",
                "SIM_CONTEXT",
            ]

        reason = build_plan_reason(
            tools,
            reassessment=False,
        )

        print(
            "\n=== GEMINI EVIDENCE PLAN ==="
        )

        print(
            "TOOLS:",
            ", ".join(tools)
        )

        print(
            "REASON:",
            reason
        )

        return {
            "evidence_plan": tools,
            "agent_reasoning": reason,
            "planning_fallback": False,
            **(
                {
                    "initial_evidence_plan": tools,
                    "initial_agent_reasoning": reason,
                }
                if not state.get("initial_evidence_plan")
                else {}
            ),
        }

    except Exception as error:

        print(
            "\n⚠️ GEMINI PLANNING UNAVAILABLE"
        )

        print(
            "Reason:",
            error
        )

        fallback = fallback_evidence_plan(
            operation,
            previous_evidence,
        )

        print(
            "\n=== DETERMINISTIC FALLBACK ==="
        )

        print(
            "TOOLS:",
            ", ".join(
                fallback["evidence_plan"]
            )
        )

        print(
            "REASON:",
            fallback["reason"]
        )

        return {
            "evidence_plan": fallback["evidence_plan"],
            "agent_reasoning": fallback["reason"],
            "planning_fallback": True,
            **(
                {
                    "initial_evidence_plan": fallback["evidence_plan"],
                    "initial_agent_reasoning": fallback["reason"],
                }
                if not state.get("initial_evidence_plan")
                else {}
            ),
        }

# ============================================================
# SAFE NETWORK CALL
# ============================================================

def safe_call(
    signal_name,
    function,
):

    try:

        result = function()

        return result, None

    except Exception as error:

        print(
            f"⚠️ {signal_name} unavailable: {error}"
        )

        return {
            "signal": signal_name,
            "result": "UNAVAILABLE",
            "raw_value": None,
            "source": (
                f"CAMARA_{signal_name}"
            ),
            "error": str(error),
        }, signal_name


# ============================================================
# NORMALIZE NETWORK EVIDENCE
#
# Raw Nokia/CAMARA values are preserved.
# ContextOS does NOT invent information.
# ============================================================

def normalize_evidence(
    signal,
    raw_result,
):

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    if signal == "LOCATION":

        raw_value = None

        if isinstance(raw_result, dict):

            raw_value = raw_result.get(
                "raw_result"
            )

            if raw_value is None:
                raw_value = raw_result.get(
                    "raw_value"
                )

        else:

            raw_value = raw_result

        if raw_value is True or str(
            raw_value
        ).upper() == "TRUE":

            result = "MATCH"

        elif raw_value is False or str(
            raw_value
        ).upper() == "FALSE":

            result = "MISMATCH"

        else:

            result = "UNAVAILABLE"

        evidence = {
            "signal": "LOCATION",
            "result": result,
            "raw_value": raw_value,
            "source": "CAMARA_LOCATION_VERIFICATION",
        }

        # Preserve API-provided metadata only.
        if isinstance(raw_result, dict):

            if "last_location_time" in raw_result:

                evidence[
                    "observed_at"
                ] = raw_result[
                    "last_location_time"
                ]

        return evidence

    # --------------------------------------------------------
    # DEVICE STATUS
    # --------------------------------------------------------

    if signal == "DEVICE_STATUS":

        raw_value = None

        if isinstance(raw_result, dict):

            raw_value = raw_result.get(
                "raw_result"
            )

            if raw_value is None:
                raw_value = raw_result.get(
                    "raw_value"
                )

        else:

            raw_value = raw_result

        # IMPORTANT:
        # Preserve CONNECTED_SMS exactly as returned.
        return {
            "signal": "CONNECTIVITY",
            "result": raw_value,
            "raw_value": raw_value,
            "source": "CAMARA_DEVICE_STATUS",
        }

    # --------------------------------------------------------
    # SIM CONTEXT
    # --------------------------------------------------------

    if signal == "SIM_CONTEXT":

        raw_value = None

        if isinstance(raw_result, dict):

            raw_value = raw_result.get(
                "raw_result"
            )

            if raw_value is None:
                raw_value = raw_result.get(
                    "raw_value"
                )

        else:

            raw_value = raw_result

        if raw_value is True:

            result = "CHANGE_DETECTED"

        elif raw_value is False:

            result = "NO_CHANGE_DETECTED"

        else:

            result = "UNAVAILABLE"

        return {
            "signal": "SIM_CONTEXT",
            "result": result,
            "raw_value": raw_value,
            "source": "CAMARA_SIM_SWAP",
        }

    return {
        "signal": signal,
        "result": "UNAVAILABLE",
        "raw_value": None,
        "source": f"CAMARA_{signal}",
    }


# ============================================================
# NODE 2 — COLLECT NETWORK EVIDENCE
# ============================================================

def collect_evidence(
    state: ContextState
):

    plan = state[
        "evidence_plan"
    ]

    print(
        "\n=== COLLECTING NETWORK EVIDENCE ==="
    )

    evidence = {}

    failures = []

    for signal in plan:

        # ====================================================
        # LOCATION
        # ====================================================

        if signal == "LOCATION":

            print(
                "Calling Location Verification..."
            )

            raw_result, failure = safe_call(
                "LOCATION",
                verify_location,
            )

            evidence[
                "location"
            ] = normalize_evidence(
                "LOCATION",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

        # ====================================================
        # DEVICE STATUS
        # ====================================================

        elif signal == "DEVICE_STATUS":

            print(
                "Calling Device Status..."
            )

            raw_result, failure = safe_call(
                "DEVICE_STATUS",
                check_connectivity,
            )

            evidence[
                "connectivity"
            ] = normalize_evidence(
                "DEVICE_STATUS",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

        # ====================================================
        # SIM CONTEXT
        # ====================================================

        elif signal == "SIM_CONTEXT":

            print(
                "Calling SIM Swap..."
            )

            raw_result, failure = safe_call(
                "SIM_CONTEXT",
                check_sim_swap,
            )

            evidence[
                "sim_swap"
            ] = normalize_evidence(
                "SIM_CONTEXT",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

    print(
        "\nStructured Network Evidence:"
    )

    print(
        json.dumps(
            evidence,
            indent=2,
        )
    )

    if failures:

        print(
            "\nUnavailable signals:"
        )

        print(
            failures
        )

    return {
        "evidence": evidence,
        "evidence_failures": failures,
    }


# ============================================================
# NODE 3 — DETERMINISTIC TRUST ENGINE
# ============================================================

def evaluate_decision(
    state: ContextState
):

    operation = state[
        "operation"
    ]

    evidence = state[
        "evidence"
    ]

    print(
        "\n=== OPERATIONAL DECISION ==="
    )

    decision = evaluate_operation(
        operation,
        evidence,
    )

    print(
        decision
    )

    return {
        "decision": decision,
    }


# ============================================================
# NODE 4 — CONTINUOUS REASSESSMENT
# ============================================================

def reassess(
    state: ContextState
):

    """
    ContextOS continuously reassesses the operation.

    Previous evidence is retained.

    Gemini determines what ADDITIONAL evidence may be useful.

    Fresh evidence is collected.

    The combined context is passed to the deterministic
    Trust Engine.

    Gemini never makes the final decision.
    """

    operation = state[
        "operation"
    ]

    previous_evidence = state.get(
        "evidence",
        {},
    )

    print("\n")
    print("=" * 60)
    print("CONTEXTOS REASSESSMENT")
    print("=" * 60)

    print(
        "\nPrevious evidence is retained."
    )

    print(
        "ContextOS will request additional "
        "evidence if required."
    )

    # ========================================================
    # GEMINI REASSESSMENT PLANNING
    # ========================================================

    print(
        "\n=== GEMINI EVIDENCE PLANNING ==="
    )

    prompt = f"""
You are the ContextOS AI agent performing continuous
operational reassessment.

Your responsibility is to determine what ADDITIONAL network
evidence is necessary to evaluate the current operational
context.

You are NOT making the final authorization decision.

The deterministic Trust Engine makes the final decision.

OPERATION:

{json.dumps(operation, indent=2)}

PREVIOUSLY COLLECTED EVIDENCE:

{json.dumps(previous_evidence, indent=2)}

AVAILABLE NETWORK CAPABILITIES:

LOCATION:
Verifies whether the device is inside the authorized area.

DEVICE_STATUS:
Returns the device's current connectivity status.
The raw result may be CONNECTED_SMS.

SIM_CONTEXT:
Reports whether a SIM change was detected.

RULES:

1. Select ONLY supported capabilities.

2. Do not invent evidence.

3. Do not make ALLOW / STEP-UP / HOLD decisions.

4. Consider what is already known.

5. Request additional evidence when it helps resolve
   uncertainty or an observed anomaly.

6. Previously collected evidence remains available,
   but it may be stale.

7. During reassessment, you may request a previously
   collected capability when its CURRENT state is
   relevant to reassessing the operation.

8. Do not request a capability merely because it exists.
   Select it only when fresh evidence can materially
   improve the operational-context evaluation.

9. If the existing evidence remains sufficient and no
   fresh signal would materially improve the assessment,
   return an empty TOOLS list.

10. A SIM swap is an identity-context anomaly,
    not automatic proof of fraud.

11. Network evidence must be interpreted in operational context.

12. The REASON must describe ONLY the capabilities listed in TOOLS.
    Do not mention a capability unless it is selected.

Return:

TOOLS: <comma-separated tools>

REASON: <brief explanation>
"""

    try:

        response = llm.invoke(
            prompt
        )

        text = extract_response_text(
            response
        )

        if not text:

            raise ValueError(
                "Gemini returned an empty reassessment response."
            )

        tools = parse_evidence_plan(
            text
        )

        # ----------------------------------------------------
        # If physical context has never been collected,
        # LOCATION is mandatory.
        # ----------------------------------------------------

        if "location" not in previous_evidence:

            if "LOCATION" not in tools:

                tools.insert(
                    0,
                    "LOCATION"
                )

        reason = build_plan_reason(
            tools,
            reassessment=True,
        )

        print(
            "\n=== GEMINI EVIDENCE PLAN ==="
        )

        print(
            "TOOLS:",
            ", ".join(tools)
        )

        print(
            "REASON:",
            reason
        )

    except Exception as error:

        print(
            "\n⚠️ GEMINI REASSESSMENT UNAVAILABLE"
        )

        print(
            "Reason:",
            error
        )

        # ----------------------------------------------------
        # SAFE FALLBACK
        # ----------------------------------------------------

        fallback = fallback_evidence_plan(
            operation,
            previous_evidence,
        )

        tools = fallback[
            "evidence_plan"
        ]

        reason = build_plan_reason(
            tools,
            reassessment=True,
        )

        print(
            "\n=== FALLBACK REASSESSMENT PLAN ==="
        )

        print(
            "TOOLS:",
            ", ".join(tools)
        )

        print(
            "REASON:",
            reason
        )

    # ========================================================
    # COLLECT NEW EVIDENCE
    # ========================================================

    print(
        "\n=== REASSESSMENT EVIDENCE PLAN ==="
    )

    print(
        "TOOLS:",
        ", ".join(tools)
    )

    new_evidence = {}

    failures = []

    for signal in tools:

        # ====================================================
        # LOCATION
        # ====================================================

        if signal == "LOCATION":

            print(
                "Calling Location Verification..."
            )

            raw_result, failure = safe_call(
                "LOCATION",
                verify_location,
            )

            new_evidence[
                "location"
            ] = normalize_evidence(
                "LOCATION",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

        # ====================================================
        # DEVICE STATUS
        # ====================================================

        elif signal == "DEVICE_STATUS":

            print(
                "Calling Device Status..."
            )

            raw_result, failure = safe_call(
                "DEVICE_STATUS",
                check_connectivity,
            )

            new_evidence[
                "connectivity"
            ] = normalize_evidence(
                "DEVICE_STATUS",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

        # ====================================================
        # SIM CONTEXT
        # ====================================================

        elif signal == "SIM_CONTEXT":

            print(
                "Calling SIM Swap..."
            )

            raw_result, failure = safe_call(
                "SIM_CONTEXT",
                check_sim_swap,
            )

            new_evidence[
                "sim_swap"
            ] = normalize_evidence(
                "SIM_CONTEXT",
                raw_result,
            )

            if failure:

                failures.append(
                    failure
                )

    # ========================================================
    # MERGE EVIDENCE
    #
    # NEVER discard previously collected context.
    # ========================================================

    combined_evidence = dict(
        previous_evidence
    )

    combined_evidence.update(
        new_evidence
    )

    print(
        "\nPrevious Evidence:"
    )

    print(
        json.dumps(
            previous_evidence,
            indent=2,
        )
    )

    print(
        "\nNew Evidence:"
    )

    print(
        json.dumps(
            new_evidence,
            indent=2,
        )
    )

    print(
        "\nCombined Operational Context:"
    )

    print(
        json.dumps(
            combined_evidence,
            indent=2,
        )
    )

    # ========================================================
    # FINAL DETERMINISTIC REASSESSMENT
    # ========================================================

    decision = evaluate_operation(
        operation,
        combined_evidence,
    )

    print(
        "\n=== REASSESSMENT DECISION ==="
    )

    print(
        decision
    )

    return {
        "evidence": combined_evidence,
        "evidence_failures": failures,
        "decision": decision,
        "agent_reasoning": reason,
        "evidence_plan": tools,
    }


# ============================================================
# BUILD LANGGRAPH
# ============================================================

def build_graph():

    graph = StateGraph(
        ContextState
    )

    # --------------------------------------------------------
    # INITIAL EVALUATION
    # --------------------------------------------------------

    graph.add_node(
        "plan_evidence",
        plan_evidence,
    )

    graph.add_node(
        "collect_evidence",
        collect_evidence,
    )

    graph.add_node(
        "evaluate_decision",
        evaluate_decision,
    )

    graph.set_entry_point(
        "plan_evidence"
    )

    graph.add_edge(
        "plan_evidence",
        "collect_evidence",
    )

    graph.add_edge(
        "collect_evidence",
        "evaluate_decision",
    )

    graph.add_edge(
        "evaluate_decision",
        END,
    )

    return graph.compile()

# ============================================================
# BUILD REASSESSMENT GRAPH
# ============================================================

def build_reassessment_graph():

    graph = StateGraph(
        ContextState
    )

    graph.add_node(
        "reassess",
        reassess,
    )

    graph.set_entry_point(
        "reassess"
    )

    graph.add_edge(
        "reassess",
        END,
    )

    return graph.compile()

# ============================================================
# RUN CONTEXTOS
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CONTEXTOS AI AGENT")
    print("=" * 60)

    operation = build_operation()

    print(
        "\nOperation:"
    )

    print(
        operation
    )

    app = build_graph()

    result = app.invoke(
        {
            "operation": operation,

            "evidence_plan": [],

            "agent_reasoning": "",

            "evidence": {},

            "decision": {},

            "previous_evidence": {},

            "planning_fallback": False,

            "evidence_failures": [],
        }
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n")

    print("=" * 60)
    print("CONTEXTOS FINAL RESULT")
    print("=" * 60)

    print(
        "\nAgent reasoning:"
    )

    print(
        result.get(
            "agent_reasoning",
            "No reasoning available.",
        )
    )

    print(
        "\nEvidence plan:"
    )

    print(
        result.get(
            "evidence_plan",
            [],
        )
    )

    print(
        "\nFinal evidence:"
    )

    print(
        json.dumps(
            result.get(
                "evidence",
                {},
            ),
            indent=2,
        )
    )

    print(
        "\nFinal decision:"
    )

    print(
        result.get(
            "decision",
            {},
        )
    )

    if result.get(
        "planning_fallback"
    ):

        print(
            "\n⚠️ Gemini was unavailable."
        )

        print(
            "The deterministic fallback policy was used."
        )

    failures = result.get(
        "evidence_failures",
        [],
    )

    if failures:

        print(
            "\n⚠️ Network signals unavailable:"
        )

        for failure in failures:

            print(
                "-",
                failure
            )