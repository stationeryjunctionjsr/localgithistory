import asyncio
import httpx
from datetime import timedelta

async def run_e2e_tests():
    print("========================================")
    print("STARTING E2E BACKEND BUSINESS LOGIC TEST")
    print("========================================")

    # 1. Generate Token
    res = httpx.post("http://localhost:8000/api/auth/login", json={
        "email": "testadmin_9678f5ff@test.com",
        "password": "Password123!"
    })
    token = res.json().get("accessToken")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Pincodes
    print("\n[1] Testing Pincodes")
    res = httpx.get("http://localhost:8000/api/pincodes", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"OK GET /pincodes. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} records.")
    else:
        print("FAIL GET /pincodes failed:", res.status_code)

    # 2. Zones
    print("\n[2] Testing Zones")
    res = httpx.get("http://localhost:8000/api/delivery-zones", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"OK GET /delivery-zones. Found {len(data)} records.")
    else:
        print("FAIL GET /delivery-zones failed:", res.status_code)

    # 3. Delivery Charges
    print("\n[3] Testing Delivery Charges")
    res = httpx.get("http://localhost:8000/api/delivery-charges", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"OK GET /delivery-charges. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} records.")
    else:
        print("FAIL GET /delivery-charges failed:", res.status_code)

    # 4. Checkout Serviceability
    print("\n[4] Testing Checkout Serviceability")
    res = httpx.get("http://localhost:8000/api/delivery-charges/check-serviceability?pincode=110001&userRole=retail", headers=headers)
    if res.status_code == 200:
        print("OK GET /check-serviceability:", res.json())
    else:
        print("FAIL GET /check-serviceability failed:", res.status_code, res.text)

    # 5. Delivery Slots
    print("\n[5] Testing Delivery Slots")
    res = httpx.get("http://localhost:8000/api/delivery-slots", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"OK GET /delivery-slots. Found {len(data['data'] if isinstance(data, dict) and 'data' in data else data)} configs.")
    else:
        print("FAIL GET /delivery-slots failed:", res.status_code)

    print("\n========================================")
    print("E2E TESTS COMPLETED")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
