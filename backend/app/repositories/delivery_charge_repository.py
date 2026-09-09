from typing import Dict, Optional

from app.db.storage_factory import get_storage


class DeliveryChargeRepository:
    def __init__(self):
        self.storage = get_storage("deliveryCharges")
        self.default_storage = get_storage("deliveryChargeDefaults")

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findByLocation(self, state: str, city: str, district: str):
        # Find city-specific charge (for backward compatibility)
        all_charges = await self.storage.findAll()
        for dc in all_charges:
            if (
                dc.get("isActive")
                and dc.get("state", "").lower() == state.lower()
                and dc.get("city", "").lower() == city.lower()
                and dc.get("district", "").lower() == district.lower()
                and not dc.get("pincode")
            ):  # Old location-based charges don't have pincode
                return dc
        return None

    async def findByPincode(self, pincode: str):
        """Find pincode-specific charge"""
        all_charges = await self.storage.findAll()
        for dc in all_charges:
            if dc.get("isActive") and dc.get("pincode") and str(dc.get("pincode")) == str(pincode):
                return dc
        return None

    async def isPincodeServiceable(self, pincode: str, user_role: str) -> bool:
        """Check if a pincode is serviceable for a user role"""
        # If pincode is not added, it's not serviceable
        charge = await self.findByPincode(pincode)
        if not charge:
            return False

        # Check serviceability based on user role
        if user_role == "customer" or not user_role:
            return charge.get("serviceableForCustomer", False) is True
        elif user_role == "wholesaler":
            return charge.get("serviceableForWholesaler", False) is True
        # All other roles (e.g. customer) use customer serviceability
        return charge.get("serviceableForCustomer", False) is True

    async def getDefaultCharge(self):
        defaults = await self.default_storage.findAll()
        return defaults[0] if defaults else None

    async def setDefaultCharge(self, default_data: Dict):
        existing = await self.getDefaultCharge()

        # Validate tiers
        if not default_data.get("tiers") or len(default_data.get("tiers", [])) == 0:
            raise ValueError("At least one tier is required for default delivery charge")

        default_charge = {
            # Only use tiers (no single charge fallback)
            "tiers": [
                {
                    "maxAmount": "Infinity" if tier.get("maxAmount") == "Infinity" else float(tier.get("maxAmount")),
                    "charge": float(tier.get("charge")),
                }
                for tier in default_data.get("tiers", [])
            ],
            # Role-based applicability
            "applicableToWholesaler": default_data.get("applicableToWholesaler", True),
            "deliveryChargeGst": default_data.get("deliveryChargeGst", False),
            "deliveryChargeGstPercentage": float(default_data.get("deliveryChargeGstPercentage", 18.0)),
            "isActive": default_data.get("isActive", True),
            "urgentDeliveryCharge": float(default_data.get("urgentDeliveryCharge"))
            if default_data.get("urgentDeliveryCharge") is not None
            else None,
        }

        if existing:
            return await self.default_storage.update(existing["_id"], default_charge)
        else:
            return await self.default_storage.create(default_charge)

    async def deleteDefaultCharge(self):
        """Delete the default delivery charge"""
        existing = await self.getDefaultCharge()
        if not existing:
            return None
        return await self.default_storage.delete(existing["_id"])

    async def getChargeForLocation(
        self,
        state: str,
        city: str,
        district: str,
        pincode: Optional[str] = None,
        user_role: str = "customer",
        order_amount: float = 0,
    ):
        # Try to find pincode-specific charge first (pincode-based always takes priority)
        pincode_charge = None
        if pincode:
            pincode_charge = await self.findByPincode(pincode)

        if pincode_charge:
            # Check if default charge is applied
            if pincode_charge.get("applyDefaultCharge"):
                default_charge = await self.getDefaultCharge()

                urgent_charge = None
                urgent_avail = False
                if default_charge:
                    urgent_charge = default_charge.get("urgentDeliveryCharge")
                    # urgent_avail = default_charge.get("urgentDeliveryAvailable", False)
                    urgent_avail = False

                if default_charge and default_charge.get("isActive"):
                    is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
                    if not is_applicable:
                        return {
                            "charge": 0,
                            "minCartValue": 0,
                            "source": "pincode-default",
                            "deliveryCharge": default_charge,
                            "isApplicableToRole": False,
                            "urgentDeliveryAvailable": urgent_avail,
                            "urgentDeliveryCharge": urgent_charge,
                        }

                    if default_charge.get("tiers") and len(default_charge.get("tiers", [])) > 0:
                        tier_charge = self.calculateTieredCharge(default_charge.get("tiers"), order_amount)
                        return {
                            "charge": tier_charge["charge"],
                            "minCartValue": tier_charge["minCartValue"],
                            "source": "pincode-default-tiered",
                            "deliveryCharge": default_charge,
                            "isApplicableToRole": True,
                            "appliedTier": tier_charge["tier"],
                            "urgentDeliveryAvailable": urgent_avail,
                            "urgentDeliveryCharge": urgent_charge,
                        }

                    return {
                        "charge": 0,
                        "minCartValue": 0,
                        "source": "pincode-default-no-tiers",
                        "deliveryCharge": default_charge,
                        "isApplicableToRole": True,
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": urgent_charge,
                    }
            else:
                # urgent_avail = pincode_charge.get("urgentDeliveryAvailable", False)
                urgent_avail = False
                # Use pincode-specific tiers or charge
                if pincode_charge.get("tiers") and len(pincode_charge.get("tiers", [])) > 0:
                    tier_charge = self.calculateTieredCharge(pincode_charge.get("tiers"), order_amount)
                    return {
                        "charge": tier_charge["charge"],
                        "minCartValue": tier_charge["minCartValue"],
                        "source": "pincode-tiered",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "appliedTier": tier_charge["tier"],
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": pincode_charge.get("urgentDeliveryCharge"),
                    }
                else:
                    return {
                        "charge": pincode_charge.get("charge", 0),
                        "minCartValue": pincode_charge.get("minCartValue", 0),
                        "source": "pincode",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": pincode_charge.get("urgentDeliveryCharge"),
                    }

        # Fallback to city-specific charge (for backward compatibility)
        city_charge = await self.findByLocation(state, city, district)

        if city_charge:
            # Check role applicability for city-specific charge
            is_applicable = self.isChargeApplicableToRole(city_charge, user_role)
            # urgent_avail = city_charge.get("urgentDeliveryAvailable", False)
            urgent_avail = False

            return {
                "charge": city_charge.get("charge", 0) if is_applicable else 0,
                "minCartValue": city_charge.get("minCartValue", 0),
                "source": "city",
                "deliveryCharge": city_charge,
                "isApplicableToRole": is_applicable,
                "urgentDeliveryAvailable": urgent_avail,
                "urgentDeliveryCharge": city_charge.get("urgentDeliveryCharge"),
            }

        # Use default if available
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.get("isActive"):
            is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
            # urgent_avail = default_charge.get("urgentDeliveryAvailable", False)
            urgent_avail = False
            urgent_charge = default_charge.get("urgentDeliveryCharge")
            
            if not is_applicable:
                return {
                    "charge": 0,
                    "minCartValue": 0,
                    "source": "default",
                    "deliveryCharge": default_charge,
                    "isApplicableToRole": False,
                    "urgentDeliveryAvailable": urgent_avail,
                    "urgentDeliveryCharge": urgent_charge,
                }

            # Default charges are always tiered (no single charge fallback)
            if default_charge.get("tiers") and len(default_charge.get("tiers", [])) > 0:
                tier_charge = self.calculateTieredCharge(default_charge.get("tiers"), order_amount)
                return {
                    "charge": tier_charge["charge"],
                    "minCartValue": tier_charge["minCartValue"],
                    "source": "default-tiered",
                    "deliveryCharge": default_charge,
                    "isApplicableToRole": True,
                    "appliedTier": tier_charge["tier"],
                    "urgentDeliveryAvailable": urgent_avail,
                    "urgentDeliveryCharge": urgent_charge,
                }

            # If no tiers configured, no delivery charge
            return {
                "charge": 0,
                "minCartValue": 0,
                "source": "default-no-tiers",
                "deliveryCharge": default_charge,
                "isApplicableToRole": True,
                "urgentDeliveryAvailable": urgent_avail,
                "urgentDeliveryCharge": urgent_charge,
            }

        return {
            "charge": 0,
            "minCartValue": 0,
            "source": "none",
            "deliveryCharge": None,
            "isApplicableToRole": True,
            "urgentDeliveryAvailable": False,
            "urgentDeliveryCharge": None,
        }

    def isChargeApplicableToRole(self, charge_data: Dict, user_role: str) -> bool:
        """Check if delivery charge is applicable to the user's role"""
        if not charge_data:
            return True  # Default to applicable if no data

        # For customers, always applicable
        if user_role == "customer" or not user_role:
            return True

        # For wholesalers
        if user_role == "wholesaler":
            return charge_data.get("applicableToWholesaler", True)  # Default to true if not specified

        return True

    def calculateTieredCharge(self, tiers: list, order_amount: float) -> Dict:
        """Calculate delivery charge based on tiered structure"""
        if not tiers or len(tiers) == 0:
            return {"charge": 0, "minCartValue": 0, "tier": None}

        # Sort tiers by maxAmount ascending
        def get_max_amount(tier):
            max_amt = tier.get("maxAmount")
            if max_amt == "Infinity" or max_amt is None:
                return float("inf")
            return float(max_amt)

        sorted_tiers = sorted(tiers, key=get_max_amount)

        # Find the applicable tier
        for tier in sorted_tiers:
            max_amount = get_max_amount(tier)

            if order_amount < max_amount:
                return {
                    "charge": float(tier.get("charge", 0)),
                    "minCartValue": max_amount if max_amount != float("inf") else 0,
                    "tier": tier,
                }

        # If no tier found, return the last tier (highest tier)
        last_tier = sorted_tiers[-1]
        return {
            "charge": float(last_tier.get("charge", 0)),
            "minCartValue": get_max_amount(last_tier) if get_max_amount(last_tier) != float("inf") else 0,
            "tier": last_tier,
        }

    async def create(self, charge_data: Dict):
        # Check if pincode already exists
        if charge_data.get("pincode"):
            existing = await self.findByPincode(charge_data.get("pincode"))
            if existing:
                raise ValueError("Pincode already exists")

        # Generate unique ID for state-district-city combination (for backward compatibility)
        all_charges = await self.storage.findAll()
        max_id = 0
        for charge in all_charges:
            if charge.get("locationId") and isinstance(charge.get("locationId"), int):
                max_id = max(max_id, charge.get("locationId", 0))
        location_id = max_id + 1

        apply_default = charge_data.get("applyDefaultCharge", False)

        charge = {
            "locationId": location_id,  # Unique ID for state-district-city (for backward compatibility)
            "pincode": charge_data.get("pincode") or None,
            "state": charge_data.get("state", ""),
            "city": charge_data.get("city", ""),
            "district": charge_data.get("district", ""),
            # If default is applied, don't store charge/minCartValue/tiers
            "applyDefaultCharge": apply_default,
            "charge": None if apply_default else float(charge_data.get("charge", 0)),
            "minCartValue": None if apply_default else float(charge_data.get("minCartValue", 0)),
            "tiers": None if apply_default else (charge_data.get("tiers", [])),
            # Serviceability flags
            "serviceableForCustomer": charge_data.get("serviceableForCustomer", False) is True,
            "serviceableForWholesaler": charge_data.get("serviceableForWholesaler", False) is True,
            "isActive": charge_data.get("isActive", True),
            "description": charge_data.get("description", ""),
            # "urgentDeliveryAvailable": charge_data.get("urgentDeliveryAvailable", False) is True,
            "urgentDeliveryAvailable": False,
            "urgentDeliveryCharge": float(charge_data.get("urgentDeliveryCharge"))
            if charge_data.get("urgentDeliveryCharge") is not None
            else None,
        }

        return await self.storage.create(charge)

    async def update(self, id: str, update_data: Dict):
        if "charge" in update_data:
            update_data["charge"] = float(update_data["charge"])
        if "minCartValue" in update_data:
            update_data["minCartValue"] = float(update_data["minCartValue"])
        if "urgentDeliveryCharge" in update_data and update_data["urgentDeliveryCharge"] is not None:
            update_data["urgentDeliveryCharge"] = float(update_data["urgentDeliveryCharge"])
        # Update role applicability if provided
        if "applicableToWholesaler" in update_data:
            update_data["applicableToWholesaler"] = bool(update_data["applicableToWholesaler"])

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)

    async def findByPinCode(self, zip_code: str):
        """Find delivery charge by pin code. If no delivery charge has been added by super admin, return None (will default to 0)"""
        # The system uses location-based charges (state, city, district), not zipCode-based
        # So we return default charge or None to use 0

        # Try to get default charge
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.get("isActive"):
            return {"charge": default_charge.get("defaultCharge", 0), "isActive": True}

        # If no default charge, return None (will be treated as 0 in order creation)
        return None


delivery_charge_repository = DeliveryChargeRepository()
