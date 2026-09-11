from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent import (
    build_graph,
    build_reassessment_graph,
    build_operation,
)


app = FastAPI(
    title="ContextOS API",
    description="Operational context verification API",
    version="1.0.0",
)


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
# Allows the React/Vite frontend to communicate with
# the Python backend during local development.
# ------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# CONTEXTOS AGENT
# ------------------------------------------------------------

contextos_app = build_graph()
reassessment_app = build_reassessment_graph()

# ------------------------------------------------------------
# IN-MEMORY OPERATION STATE
# ------------------------------------------------------------
# Keeps the latest evidence for the current demo operation
# across reassessment requests.
# ------------------------------------------------------------

operation_state = {
    "previous_evidence": {},
    "initial_evidence_plan": [],
    "initial_agent_reasoning": "",
    "planning_fallback": False,
    "assessment_type": "initial",
}

# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ContextOS",
    }


# ------------------------------------------------------------
# OPERATION
# ------------------------------------------------------------

@app.get("/operation")
def get_operation():

    operation = build_operation()

    return {
        "operation": operation,
    }

# ------------------------------------------------------------
# RESET DEMO STATE
# ------------------------------------------------------------

@app.post("/reset")
def reset_demo():

    operation_state["previous_evidence"] = {}
    operation_state["initial_evidence_plan"] = []
    operation_state["initial_agent_reasoning"] = ""
    operation_state["planning_fallback"] = False
    operation_state["assessment_type"] = "initial"

    return {
        "status": "reset",
        "message": "ContextOS demo state has been reset.",
    }
# ------------------------------------------------------------
# FULL CONTEXTOS EVALUATION
# ------------------------------------------------------------

@app.post("/reassess")
def reassess():

    operation = build_operation()

    previous_evidence = operation_state[
        "previous_evidence"
    ]

    # ========================================================
    # INITIAL ASSESSMENT
    #
    # If no evidence exists yet, run the INITIAL graph.
    # ========================================================

    if not previous_evidence:

        result = contextos_app.invoke(
            {
                "operation": operation,

                "evidence_plan": [],

                "agent_reasoning": "",

                "initial_evidence_plan": [],

                "initial_agent_reasoning": "",

                "evidence": {},

                "decision": {},

                "previous_evidence": {},

                "planning_fallback": False,

                "evidence_failures": [],
            }
        )

    # ========================================================
    # CONTINUOUS REASSESSMENT
    #
    # If evidence already exists, run the reassessment graph.
    # ========================================================

    else:

        result = reassessment_app.invoke(
            {
                "operation": operation,

                "evidence_plan": [],

                "agent_reasoning": "",

                "initial_evidence_plan": operation_state[
                    "initial_evidence_plan"
                ],

                "initial_agent_reasoning": operation_state[
                    "initial_agent_reasoning"
                ],

                "evidence": previous_evidence,

                "decision": {},

                "previous_evidence": previous_evidence,

                "planning_fallback": False,

                "evidence_failures": [],
            }
        )

    # ========================================================
    # SAVE CURRENT EVIDENCE
    # ========================================================

    operation_state[
        "previous_evidence"
    ] = result.get(
        "evidence",
        previous_evidence,
    )

    # ========================================================
    # SAVE INITIAL AGENT ASSESSMENT
    # ========================================================

    operation_state[
        "initial_evidence_plan"
    ] = result.get(
        "initial_evidence_plan",
        operation_state["initial_evidence_plan"],
    )

    operation_state[
        "initial_agent_reasoning"
    ] = result.get(
        "initial_agent_reasoning",
        operation_state["initial_agent_reasoning"],
    )

    operation_state["planning_fallback"] = result.get(
        "planning_fallback",
        operation_state["planning_fallback"],
    )

    operation_state["assessment_type"] = result.get(
        "assessment_type",
        operation_state["assessment_type"],
    )

    return result