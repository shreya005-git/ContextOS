from trust_engine import evaluate_operation


operation = {
    "name": "Network equipment replacement",
    "risk": "HIGH"
}


evidence = {
    "location": {
        "raw_result": "TRUE"
    },
    "connectivity": {
        "raw_result": "CONNECTED_SMS"
    },
    "sim_swap": {
        "raw_result": True
    }
}


result = evaluate_operation(operation, evidence)

print(result)