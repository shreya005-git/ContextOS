# ============================================================
# CONTEXTOS TRUST ENGINE
#
# Deterministic operational decision layer.
#
# Gemini does NOT make the final authorization decision.
# ============================================================


def evaluate_operation(operation, evidence):
    """
    Evaluate observed network evidence against the
    expected operational context.

    Possible decisions:

        ALLOW
        STEP-UP
        HOLD

    The LLM never overrides this function.
    """

    risk = operation.get("risk")

    location = evidence.get("location")
    connectivity = evidence.get("connectivity")
    sim_context = evidence.get("sim_swap")


    # ========================================================
    # 1. PHYSICAL CONTEXT
    #
    # A strong location conflict causes HOLD.
    # ========================================================

    if location:

        raw_location = location.get(
            "raw_value"
        )

        location_result = location.get(
            "result"
        )

        if (
            raw_location == "FALSE"
            or location_result == "MISMATCH"
        ):

            return {
                "decision": "HOLD",

                "reason": (
                    "The observed physical context "
                    "conflicts with the expected "
                    "operational location. The operation "
                    "should be temporarily stopped "
                    "pending investigation."
                ),
            }


    # ========================================================
    # 2. REQUIRED EVIDENCE
    #
    # Missing evidence must never silently become ALLOW.
    # ========================================================

    if risk == "HIGH":

        if (
            location is None
            or location.get("result") == "UNAVAILABLE"
            or location.get("raw_value") is None
        ):
            return {
                "decision": "STEP-UP",
                "reason": (
                    "Location evidence is unavailable. "
                    "The physical operational context "
                    "cannot be established for this "
                    "high-risk operation."
                ),
            }

        if (
            sim_context is None
            or sim_context.get("result") == "UNAVAILABLE"
            or sim_context.get("raw_value") is None
        ):
            return {
                "decision": "STEP-UP",
                "reason": (
                    "Identity-context evidence is unavailable. "
                    "Additional verification is required "
                    "before proceeding with this high-risk "
                    "operation."
                ),
            }

    # ========================================================
    # 3. SIM CONTEXT
    #
    # SIM swap = anomaly, NOT automatic proof of fraud.
    # ========================================================

    if sim_context:

        raw_sim = sim_context.get(
            "raw_value"
        )

        sim_result = sim_context.get(
            "result"
        )

        if (
            raw_sim is True
            or sim_result == "CHANGE_DETECTED"
        ):

            return {
                "decision": "STEP-UP",

                "reason": (
                    "Physical context is consistent, "
                    "but the identity context contains "
                    "an anomaly. Because this is a "
                    "high-risk operation, additional "
                    "verification is required."
                ),
            }


    # ========================================================
    # 4. DEVICE CONNECTIVITY
    #
    # IMPORTANT:
    #
    # CONNECTED_SMS is a valid Nokia response.
    # It must NOT be treated as DISCONNECTED.
    # ========================================================

    if connectivity:

        raw_connectivity = connectivity.get(
            "raw_value"
        )

        if raw_connectivity not in [
            "CONNECTED_SMS",
            "CONNECTED_DATA",
        ]:

            return {
                "decision": "STEP-UP",

                "reason": (
                    "The device connectivity context "
                    "is unavailable or inconsistent "
                    "with the expected operational context."
                ),
            }


    # ========================================================
    # 5. ALLOW
    # ========================================================

    return {
        "decision": "ALLOW",

        "reason": (
            "The available evidence is sufficiently "
            "consistent with the expected operational "
            "context for this operation."
        ),
    }