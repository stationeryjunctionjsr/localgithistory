import pytest
from app.routers.delivery_charges import check_serviceability


@pytest.mark.asyncio
async def test_invalid_pincode_format():
    res = await check_serviceability("123", "customer")
    assert res["isServiceable"] is False
    assert res["pincode"] == "123"
    assert res["sellerCount"] == 0

    res_letters = await check_serviceability("ABCDEF", "customer")
    assert res_letters["isServiceable"] is False


@pytest.mark.asyncio
async def test_unserviceable_pincode():
    # Pincode not configured in system
    res = await check_serviceability("999999", "customer")
    assert res["isServiceable"] is False
    assert res["pincode"] == "999999"
    assert res["sellerCount"] == 0
