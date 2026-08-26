import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_auth_flow():
    print("Testing auth flow...")
    
    # 1. Test check-phone
    phone = "9999999999"
    try:
        r = requests.post(f"{BASE_URL}/auth/check-phone", json={"phone": phone})
        print(f"check-phone: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"check-phone error: {e}")

    # 2. Test send-otp
    try:
        r = requests.post(f"{BASE_URL}/auth/send-otp", json={"phone": phone, "purpose": "login"})
        print(f"send-otp: {r.status_code} - {r.text}")
        otp = r.json().get("otp") if r.status_code == 200 else None
    except Exception as e:
        print(f"send-otp error: {e}")

    # 3. Test login if we get OTP, wait login uses password
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json={"phone": phone, "password": "password123"})
        print(f"login: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"login error: {e}")

if __name__ == "__main__":
    test_auth_flow()
