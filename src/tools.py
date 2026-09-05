import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from network_as_code import NetworkAsCodeApi


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("NAC_API_KEY")

if not api_key:
    raise ValueError(
        "NAC_API_KEY was not found in .env"
    )


# ============================================================
# NOKIA NETWORK AS CODE
# ============================================================

client = NetworkAsCodeApi(
    rapidapi_host="network-as-code.nokia.rapidapi.com",
    api_key=api_key,
)


# ============================================================
# TEST DEVICE
# ============================================================

TEST_DEVICE = {
    "phoneNumber": "+9999123456"
}


# ============================================================
# LOCATION VERIFICATION
# ============================================================

def verify_location():
    """
    Verify whether the test device is inside
    the authorized operational area.

    The raw Nokia result is preserved.
    """

    result = client.location.verify(
        device=TEST_DEVICE,
        area={
            "areaType": "CIRCLE",
            "center": {
                "latitude": 50.735851,
                "longitude": 7.10066
            },
            "radius": 50000
        }
    )

    return {
        "signal": "LOCATION",

        "result": (
            "MATCH"
            if result.verification_result == "TRUE"
            else "MISMATCH"
            if result.verification_result == "FALSE"
            else "UNKNOWN"
        ),

        "raw_value": result.verification_result,

        "source": "CAMARA_LOCATION_VERIFICATION",

        "observed_at": str(
            result.last_location_time
        ),
    }


# ============================================================
# DEVICE CONNECTIVITY
# ============================================================

def check_connectivity():
    """
    Check the device's current network connectivity.

    The raw Nokia response is preserved exactly.
    Example:
        CONNECTED_SMS
    """

    result = client.device_status.check_connectivity(
        device=TEST_DEVICE
    )

    return {
        "signal": "CONNECTIVITY",

        "result": result.connectivity_status,

        "raw_value": result.connectivity_status,

        "source": "CAMARA_DEVICE_STATUS",

        # We do NOT invent an observed_at timestamp
        # because the API response shown by the user
        # does not provide one.
    }


# ============================================================
# SIM SWAP
# ============================================================

def check_sim_swap():
    """
    Check whether the SIM Swap capability reports
    a detected SIM change.

    A positive result is treated as an
    identity-context anomaly.

    We do NOT claim when the SIM change occurred
    because the API does not provide that information.
    """

    result = client.sim_swap.check(
        phone_number=TEST_DEVICE["phoneNumber"]
    )

    return {
        "signal": "SIM_CONTEXT",

        "result": (
            "CHANGE_DETECTED"
            if result.swapped is True
            else "NO_CHANGE_DETECTED"
            if result.swapped is False
            else "UNKNOWN"
        ),

        "raw_value": result.swapped,

        "source": "CAMARA_SIM_SWAP",
    }