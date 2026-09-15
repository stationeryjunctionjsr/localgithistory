from typing import Any
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
                (dc["isActive"] if "isActive" in dc else None)
                and (dc["state"] if "state" in dc else "").lower() == (state or "").lower()
                and (dc["city"] if "city" in dc else "").lower() == (city or "").lower()
                and (dc["district"] if "district" in dc else "").lower() == (district or "").lower()
                and not (dc["pincode"] if "pincode" in dc else None)
            ):  # Old location-based charges don't have pincode
                return dc
        return None

    async def findByPincode(self, pincode: str):
        """Find pincode-specific charge"""
        all_charges = await self.storage.findAll()
        for dc in all_charges:
            if (dc["isActive"] if "isActive" in dc else None) and (dc["pincode"] if "pincode" in dc else None) and str((dc["pincode"] if "pincode" in dc else None)) == str(pincode):
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
            return (charge["serviceableForCustomer"] if "serviceableForCustomer" in charge else False) is True
        elif user_role == "wholesaler":
            return (charge["serviceableForWholesaler"] if "serviceableForWholesaler" in charge else False) is True
        # All other roles (e.g. customer) use customer serviceability
        return (charge["serviceableForCustomer"] if "serviceableForCustomer" in charge else False) is True

    async def getDefaultCharge(self):
        defaults = await self.default_storage.findAll()
        return defaults[0] if defaults else None

    async def setDefaultCharge(self, default_data: Any):
        existing = await self.getDefaultCharge()

        # Validate tiers
        if not (default_data["tiers"] if "tiers" in default_data else None) or len((default_data["tiers"] if "tiers" in default_data else [])) == 0:
            raise ValueError("At least one tier is required for default delivery charge")

        default_charge = {
            # Only use tiers (no single charge fallback)
            "tiers": [
                {
                    "maxAmount": "Infinity" if (tier["maxAmount"] if "maxAmount" in tier else None) == "Infinity" else float((tier["maxAmount"] if "maxAmount" in tier else None)),
                    "charge": float((tier["charge"] if "charge" in tier else None)),
                }
                for tier in (default_data["tiers"] if "tiers" in default_data else [])
            ],
            # Role-based applicability
            "applicableToWholesaler": (default_data["applicableToWholesaler"] if "applicableToWholesaler" in default_data else True),
            "deliveryChargeGst": (default_data["deliveryChargeGst"] if "deliveryChargeGst" in default_data else False),
            "deliveryChargeGstPercentage": float((default_data["deliveryChargeGstPercentage"] if "deliveryChargeGstPercentage" in default_data else 18.0)),
            "isActive": (default_data["isActive"] if "isActive" in default_data else True),
            "urgentDeliveryCharge": float((default_data["urgentDeliveryCharge"] if "urgentDeliveryCharge" in default_data else None))
            if (default_data["urgentDeliveryCharge"] if "urgentDeliveryCharge" in default_data else None) is not None
            else None,
        }

        if existing:
            return await self.default_storage.update(existing.id, default_charge)
        else:
            return await self.default_storage.create(default_charge)

    async def deleteDefaultCharge(self):
        """Delete the default delivery charge"""
        existing = await self.getDefaultCharge()
        if not existing:
            return None
        return await self.default_storage.delete(existing.id)

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
            if (pincode_charge["applyDefaultCharge"] if "applyDefaultCharge" in pincode_charge else None):
                default_charge = await self.getDefaultCharge()

                urgent_charge = None
                urgent_avail = False
                if default_charge:
                    urgent_charge = (default_charge["urgentDeliveryCharge"] if "urgentDeliveryCharge" in default_charge else None)
                    # urgent_avail = (default_charge["urgentDeliveryAvailable"] if "urgentDeliveryAvailable" in default_charge else False)
                    urgent_avail = False

                if default_charge and (default_charge["isActive"] if "isActive" in default_charge else None):
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

                    if (default_charge["tiers"] if "tiers" in default_charge else None) and len((default_charge["tiers"] if "tiers" in default_charge else [])) > 0:
                        tier_charge = self.calculateTieredCharge((default_charge["tiers"] if "tiers" in default_charge else None), order_amount)
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
                # urgent_avail = (pincode_charge["urgentDeliveryAvailable"] if "urgentDeliveryAvailable" in pincode_charge else False)
                urgent_avail = False
                # Use pincode-specific tiers or charge
                if (pincode_charge["tiers"] if "tiers" in pincode_charge else None) and len((pincode_charge["tiers"] if "tiers" in pincode_charge else [])) > 0:
                    tier_charge = self.calculateTieredCharge((pincode_charge["tiers"] if "tiers" in pincode_charge else None), order_amount)
                    return {
                        "charge": tier_charge["charge"],
                        "minCartValue": tier_charge["minCartValue"],
                        "source": "pincode-tiered",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "appliedTier": tier_charge["tier"],
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": (pincode_charge["urgentDeliveryCharge"] if "urgentDeliveryCharge" in pincode_charge else None),
                    }
                else:
                    return {
                        "charge": (pincode_charge["charge"] if "charge" in pincode_charge else 0),
                        "minCartValue": (pincode_charge["minCartValue"] if "minCartValue" in pincode_charge else 0),
                        "source": "pincode",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": (pincode_charge["urgentDeliveryCharge"] if "urgentDeliveryCharge" in pincode_charge else None),
                    }

        # Fallback to city-specific charge (for backward compatibility)
        city_charge = await self.findByLocation(state, city, district)

        if city_charge:
            # Check role applicability for city-specific charge
            is_applicable = self.isChargeApplicableToRole(city_charge, user_role)
            # urgent_avail = (city_charge["urgentDeliveryAvailable"] if "urgentDeliveryAvailable" in city_charge else False)
            urgent_avail = False

            return {
                "charge": (city_charge["charge"] if "charge" in city_charge else 0) if is_applicable else 0,
                "minCartValue": (city_charge["minCartValue"] if "minCartValue" in city_charge else 0),
                "source": "city",
                "deliveryCharge": city_charge,
                "isApplicableToRole": is_applicable,
                "urgentDeliveryAvailable": urgent_avail,
                "urgentDeliveryCharge": (city_charge["urgentDeliveryCharge"] if "urgentDeliveryCharge" in city_charge else None),
            }

        # Use default if available
        default_charge = await self.getDefaultCharge()
        if default_charge and (default_charge["isActive"] if "isActive" in default_charge else None):
            is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
            # urgent_avail = (default_charge["urgentDeliveryAvailable"] if "urgentDeliveryAvailable" in default_charge else False)
            urgent_avail = False
            urgent_charge = (default_charge["urgentDeliveryCharge"] if "urgentDeliveryCharge" in default_charge else None)
            
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
            if (default_charge["tiers"] if "tiers" in default_charge else None) and len((default_charge["tiers"] if "tiers" in default_charge else [])) > 0:
                tier_charge = self.calculateTieredCharge((default_charge["tiers"] if "tiers" in default_charge else None), order_amount)
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

    def isChargeApplicableToRole(self, charge_data: Any, user_role: str) -> bool:
        """Check if delivery charge is applicable to the user's role"""
        if not charge_data:
            return True  # Default to applicable if no data

        # For customers, always applicable
        if user_role == "customer" or not user_role:
            return True

        # For wholesalers
        if user_role == "wholesaler":
            return (charge_data["applicableToWholesaler"] if "applicableToWholesaler" in charge_data else True)  # Default to true if not specified

        return True

    def calculateTieredCharge(self, tiers: list, order_amount: float) -> Dict:
        """Calculate delivery charge based on tiered structure"""
        if not tiers or len(tiers) == 0:
            return {"charge": 0, "minCartValue": 0, "tier": None}

        # Sort tiers by maxAmount ascending
        def get_max_amount(tier):
            max_amt = (tier["maxAmount"] if "maxAmount" in tier else None)
            if max_amt == "Infinity" or max_amt is None:
                return float("inf")
            return float(max_amt)

        sorted_tiers = sorted(tiers, key=get_max_amount)

        # Find the applicable tier
        for tier in sorted_tiers:
            max_amount = get_max_amount(tier)

            if order_amount < max_amount:
                return {
                    "charge": float((tier["charge"] if "charge" in tier else None)),
                    "minCartValue": max_amount if max_amount != float("inf") else 0,
                    "tier": tier,
                }

        # If no tier found, return the last tier (highest tier)
        last_tier = sorted_tiers[-1]
        return {
            "charge": float((last_tier["charge"] if "charge" in last_tier else None)),
            "minCartValue": get_max_amount(last_tier) if get_max_amount(last_tier) != float("inf") else 0,
            "tier": last_tier,
        }

    async def create(self, charge_data: Any):
        # Check if pincode already exists
        if (charge_data["pincode"] if "pincode" in charge_data else None):
            existing = await self.findByPincode((charge_data["pincode"] if "pincode" in charge_data else None))
            if existing:
                raise ValueError("Pincode already exists")

        # Generate unique ID for state-district-city combination (for backward compatibility)
        all_charges = await self.storage.findAll()
        max_id = 0
        for charge in all_charges:
            if (charge["locationId"] if "locationId" in charge else None) and isinstance((charge["locationId"] if "locationId" in charge else None), int):
                max_id = max(max_id, (charge["locationId"] if "locationId" in charge else 0))
        location_id = max_id + 1

        apply_default = (charge_data["applyDefaultCharge"] if "applyDefaultCharge" in charge_data else False)

        charge = {
            "locationId": location_id,  # Unique ID for state-district-city (for backward compatibility)
            "pincode": (charge_data["pincode"] if "pincode" in charge_data else None) or None,
            "state": (charge_data["state"] if "state" in charge_data else ""),
            "city": (charge_data["city"] if "city" in charge_data else ""),
            "district": (charge_data["district"] if "district" in charge_data else ""),
            # If default is applied, don't store charge/minCartValue/tiers
            "applyDefaultCharge": apply_default,
            "charge": None if apply_default else (float((charge_data["charge"] if "charge" in charge_data else None)) if (charge_data["charge"] if "charge" in charge_data else None) is not None else None),
            "minCartValue": None if apply_default else (float((charge_data["minCartValue"] if "minCartValue" in charge_data else None)) if (charge_data["minCartValue"] if "minCartValue" in charge_data else None) is not None else None),
            "tiers": None if apply_default else ((charge_data["tiers"] if "tiers" in charge_data else [])),
            # Serviceability flags
            "serviceableForCustomer": (charge_data["serviceableForCustomer"] if "serviceableForCustomer" in charge_data else False) is True,
            "serviceableForWholesaler": (charge_data["serviceableForWholesaler"] if "serviceableForWholesaler" in charge_data else False) is True,
            "isActive": (charge_data["isActive"] if "isActive" in charge_data else True),
            "description": (charge_data["description"] if "description" in charge_data else ""),
            # "urgentDeliveryAvailable": (charge_data["urgentDeliveryAvailable"] if "urgentDeliveryAvailable" in charge_data else False) is True,
            "urgentDeliveryAvailable": False,
            "urgentDeliveryCharge": float((charge_data["urgentDeliveryCharge"] if "urgentDeliveryCharge" in charge_data else None))
            if (charge_data["urgentDeliveryCharge"] if "urgentDeliveryCharge" in charge_data else None) is not None
            else None,
        }

        return await self.storage.create(charge)

    async def update(self, id: str, update_data: Any):
        if "charge" in update_data:
            update_data.charge = float(update_data.charge)
        if "minCartValue" in update_data:
            update_data.minCartValue = float(update_data.minCartValue)
        if "urgentDeliveryCharge" in update_data and update_data.urgentDeliveryCharge is not None:
            update_data.urgentDeliveryCharge = float(update_data.urgentDeliveryCharge)
        # Update role applicability if provided
        if "applicableToWholesaler" in update_data:
            update_data.applicableToWholesaler = bool(update_data.applicableToWholesaler)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)

    async def findByPinCode(self, zip_code: str):
        """Find delivery charge by pin code. If no delivery charge has been added by super admin, return None (will default to 0)"""
        # The system uses location-based charges (state, city, district), not zipCode-based
        # So we return default charge or None to use 0

        # Try to get default charge
        default_charge = await self.getDefaultCharge()
        if default_charge and (default_charge["isActive"] if "isActive" in default_charge else None):
            return {"charge": (default_charge["defaultCharge"] if "defaultCharge" in default_charge else 0), "isActive": True}

        # If no default charge, return None (will be treated as 0 in order creation)
        return None


delivery_charge_repository = DeliveryChargeRepository()


