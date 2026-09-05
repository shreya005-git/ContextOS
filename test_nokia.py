import os
from dotenv import load_dotenv
from network_as_code import NetworkAsCodeApi

load_dotenv()

api_key = os.getenv("NAC_API_KEY")

if not api_key:
    raise ValueError("NAC_API_KEY was not found in .env")

client = NetworkAsCodeApi(
    rapidapi_host="network-as-code.nokia.rapidapi.com",
    api_key=api_key,
)

print("✅ Nokia Network as Code client created successfully!")
result = client.sim_swap.check(
    phone_number="+9999123456"
)

print("SIM Swap result:")
print(result)