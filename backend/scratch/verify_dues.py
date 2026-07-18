import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.repositories.user_repository import user_repository
from app.repositories.payment_repository import payment_repository
from app.repositories.order_repository import order_repository
from app.routers.payments import get_wholesaler_dues
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta

async def run_verification():
    print("--- Starting Dues Block Verification Script ---")
    
    # 1. Create a dummy wholesaler user
    email = f"verify_wholesaler@example.com"
    user_data = {
        "name": "Verify Wholesaler",
        "email": email,
        "password": "password123",
        "role": "wholesaler",
        "paymentTerms": "30",
        "creditLimit": 10000.0,
        "creditUsed": 0.0
    }
    # Check if user already exists
    existing = await user_repository.findOne({"email": email})
    if existing:
        await user_repository.storage.delete(existing["_id"])
        
    user = await user_repository.create(user_data)
    print(f"Created wholesaler user: ID {user['_id']}, Name: {user['name']}")
    
    payment = None
    try:
        # Test 1: Fetch dues of a fresh user
        dues = await get_wholesaler_dues(current_user=user)
        print("Dues for fresh wholesaler user:")
        print(f"  hasOverdueBills: {dues['hasOverdueBills']} (expected: False)")
        print(f"  totalDues: {dues['totalDues']} (expected: 0)")
        assert dues["hasOverdueBills"] is False
        assert dues["totalDues"] == 0
        
        # Test 2: Create a credit payment that is overdue (35 days old)
        order_date = datetime.now(timezone.utc) - timedelta(days=35)
        payment_data = {
            "orderId": "verify_order_123",
            "userId": user["userId"],
            "customerName": user["name"],
            "orderDate": order_date.isoformat().replace("+00:00", "Z"),
            "paymentMethod": "credit",
            "amountPaid": 0.0,
            "amountRemaining": 850.0,
            "totalAmount": 850.0,
        }
        payment = await payment_repository.create(payment_data)
        print(f"Created credit payment of 850.0 dated {payment_data['orderDate']}")
        
        # Test 3: Fetch dues with overdue credit payment
        dues = await get_wholesaler_dues(current_user=user)
        print("Dues with overdue bill:")
        print(f"  hasOverdueBills: {dues['hasOverdueBills']} (expected: True)")
        print(f"  totalDues: {dues['totalDues']} (expected: 850.0)")
        print(f"  nearestDueAmount: {dues['nearestDueAmount']} (expected: 850.0)")
        assert dues["hasOverdueBills"] is True
        assert dues["totalDues"] == 850.0
        assert len(dues["bills"]) == 1
        print(f"  Bill remaining time: '{dues['bills'][0]['timeRemaining']}'")
        assert "Overdue" in dues["bills"][0]["timeRemaining"]

        # Test 4: Simulate backend blocking logic (mimic orders.py create_order block check)
        print("Verifying order placement block logic...")
        # Get latest user doc
        user_doc = await user_repository.findById(user["_id"])
        
        # Run block check logic
        has_overdue = False
        user_payments = await payment_repository.findAll({"userId": user_doc.get("userId")})
        now = datetime.utcnow()
        for p in user_payments:
            if p.get("paymentMethod") == "credit":
                verified_paid = sum(
                    entry.get("amount", 0.0)
                    for entry in p.get("paymentEntries", [])
                    if entry.get("verified")
                )
                effective_due = p.get("totalAmount", 0.0) - verified_paid
                if effective_due > 0:
                    order_date_str = p.get("orderDate") or p.get("createdAt")
                    if order_date_str:
                        order_date = datetime.fromisoformat(order_date_str.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
                        due_date = order_date + timedelta(days=30)
                        if now > due_date:
                            has_overdue = True
                            break
        print(f"  Block condition check: has_overdue = {has_overdue} (expected: True)")
        assert has_overdue is True
        
        # Test 5: Add a payment entry but keep it unverified
        print("Submitting settlement screenshot (verified = False)...")
        updated_payment = await payment_repository.addPaymentEntry(
            payment["_id"], {"amount": 850.0, "image": "screenshot.png", "verified": False}
        )
        
        # Fetch dues again. Because the entry is not verified, it should STILL be overdue!
        dues = await get_wholesaler_dues(current_user=user)
        print("Dues after submitting settlement screenshot (unverified):")
        print(f"  hasOverdueBills: {dues['hasOverdueBills']} (expected: True)")
        print(f"  totalDues: {dues['totalDues']} (expected: 850.0)")
        assert dues["hasOverdueBills"] is True
        assert dues["totalDues"] == 850.0
        
        # Test 6: Verify the payment entry (simulating admin verification)
        print("Verifying payment entry (simulating admin action)...")
        entries = updated_payment.get("paymentEntries", [])
        entry_id = entries[0]["entryId"]
        await payment_repository.updatePaymentEntry(payment["_id"], entry_id, {"verified": True})
        
        # Fetch dues again. Now the overdue block should be lifted!
        dues = await get_wholesaler_dues(current_user=user)
        print("Dues after admin verification:")
        print(f"  hasOverdueBills: {dues['hasOverdueBills']} (expected: False)")
        print(f"  totalDues: {dues['totalDues']} (expected: 0.0)")
        assert dues["hasOverdueBills"] is False
        assert dues["totalDues"] == 0.0
        
        print("\n=== ALL BACKEND VERIFICATIONS PASSED SUCCESSFULLY! ===")
        
    finally:
        # Cleanup user and payment
        print("Cleaning up database entries...")
        await user_repository.storage.delete(user["_id"])
        if payment:
            await payment_repository.delete(payment["_id"])
        print("Cleanup done.")

if __name__ == "__main__":
    asyncio.run(run_verification())
