from typing import Any
from app.models.daos_flat import DeliveryChargeInternal, DeliveryChargeDefaultInternal, DeliveryChargeInternalCreate, DeliveryChargeInternalUpdate, DeliveryChargeDefaultInternalCreate, DeliveryChargeDefaultInternalUpdate, DeliveryChargeTierInternal
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class DeliveryChargeRepository:
    def __init__(self):
        self.storage = get_storage("deliveryCharges")
        self.default_storage = get_storage("deliveryChargeDefaults")

    async def findAll(self, query: Optional[Dict] = None) -> list[DeliveryChargeInternal]:
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findByLocation(self, state: str, city: str, district: str):
        # Find city-specific charge (for backward compatibility)
        all_charges = await self.storage.findAll()
        for dc in all_charges:
            if (
                dc.isActive
                and dc.state.lower() == (state or "").lower()
                and dc.city.lower() == (city or "").lower()
                and dc.district.lower() == (district or "").lower()
                and not dc.pincode
            ):  # Old location-based charges don't have pincode
                return dc
        return None

    async def findByPincode(self, pincode: str):
        """Find pincode-specific charge"""
        all_charges = await self.storage.findAll()
        for dc in all_charges:
            if dc.isActive and dc.pincode and str(dc.pincode) == str(pincode):
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
            return charge.serviceableForCustomer is True
        elif user_role == "wholesaler":
            return charge.serviceableForWholesaler is True
        # All other roles (e.g. customer) use customer serviceability
        return charge.serviceableForCustomer is True

    async def getDefaultCharge(self) -> Optional[DeliveryChargeDefaultInternal]:
        defaults = await self.default_storage.findAll()
        return defaults[0] if defaults else None

    async def setDefaultCharge(self, default_data: DeliveryChargeDefaultInternalCreate) -> DeliveryChargeDefaultInternal:
        existing = await self.getDefaultCharge()

        # Validate tiers
        if not default_data.tiers or len(default_data.tiers) == 0:
            raise ValueError("At least one tier is required for default delivery charge")

        from app.models.daos_flat import DeliveryChargeTierInternal
        tiers_internal = [
            DeliveryChargeTierInternal(
                max=float('inf') if tier.maxAmount == "Infinity" else float(tier.maxAmount),
                charge=float(tier.charge)
            )
            for tier in default_data.tiers
        ]

        default_charge = DeliveryChargeDefaultInternalUpdate(
            applicableToWholesaler=default_data.applicableToWholesaler,
            isActive=default_data.isActive,
            tiers=tiers_internal
        )

        if existing:
            return await self.default_storage.update(existing.id, default_charge)
        else:
            default_create = DeliveryChargeDefaultInternalCreate(
                applicableToWholesaler=default_data.applicableToWholesaler,
                isActive=default_data.isActive,
                tiers=tiers_internal
            )
            return await self.default_storage.create(default_create)

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
            if pincode_charge.applyDefaultCharge:
                default_charge = await self.getDefaultCharge()

                urgent_charge = None
                urgent_avail = False
                if default_charge:
                    urgent_charge = default_charge.urgentDeliveryCharge
                    # urgent_avail = default_charge.urgentDeliveryAvailable
                    urgent_avail = False

                if default_charge and default_charge.isActive:
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

                    if default_charge.tiers and len(default_charge.tiers) > 0:
                        tier_charge = self.calculateTieredCharge(default_charge.tiers, order_amount)
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
                # urgent_avail = pincode_charge.urgentDeliveryAvailable
                urgent_avail = False
                # Use pincode-specific tiers or charge
                if pincode_charge.tiers and len(pincode_charge.tiers) > 0:
                    tier_charge = self.calculateTieredCharge(pincode_charge.tiers, order_amount)
                    return {
                        "charge": tier_charge["charge"],
                        "minCartValue": tier_charge["minCartValue"],
                        "source": "pincode-tiered",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "appliedTier": tier_charge["tier"],
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": pincode_charge.urgentDeliveryCharge,
                    }
                else:
                    return {
                        "charge": pincode_charge.charge,
                        "minCartValue": pincode_charge.minCartValue,
                        "source": "pincode",
                        "deliveryCharge": pincode_charge,
                        "isApplicableToRole": True,
                        "urgentDeliveryAvailable": urgent_avail,
                        "urgentDeliveryCharge": pincode_charge.urgentDeliveryCharge,
                    }

        # Fallback to city-specific charge (for backward compatibility)
        city_charge = await self.findByLocation(state, city, district)

        if city_charge:
            # Check role applicability for city-specific charge
            is_applicable = self.isChargeApplicableToRole(city_charge, user_role)
            # urgent_avail = city_charge.urgentDeliveryAvailable
            urgent_avail = False

            return {
                "charge": city_charge.charge if is_applicable else 0,
                "minCartValue": city_charge.minCartValue,
                "source": "city",
                "deliveryCharge": city_charge,
                "isApplicableToRole": is_applicable,
                "urgentDeliveryAvailable": urgent_avail,
                "urgentDeliveryCharge": city_charge.urgentDeliveryCharge,
            }

        # Use default if available
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.isActive:
            is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
            # urgent_avail = default_charge.urgentDeliveryAvailable
            urgent_avail = False
            urgent_charge = default_charge.urgentDeliveryCharge
            
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
            if default_charge.tiers and len(default_charge.tiers) > 0:
                tier_charge = self.calculateTieredCharge(default_charge.tiers, order_amount)
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
            return charge_data.applicableToWholesaler  # Default to true if not specified

        return True

    def calculateTieredCharge(self, tiers: list, order_amount: float) -> Dict:
        """Calculate delivery charge based on tiered structure"""
        if not tiers or len(tiers) == 0:
            return {"charge": 0, "minCartValue": 0, "tier": None}

        # Sort tiers by maxAmount ascending
        def get_max_amount(tier):
            max_amt = tier.max
            if max_amt == "Infinity" or max_amt is None:
                return float("inf")
            return float(max_amt)

        sorted_tiers = sorted(tiers, key=get_max_amount)

        # Find the applicable tier
        for tier in sorted_tiers:
            max_amount = get_max_amount(tier)

            if order_amount < max_amount:
                return {
                    "charge": float(tier.charge),
                    "minCartValue": max_amount if max_amount != float("inf") else 0,
                    "tier": tier,
                }

        # If no tier found, return the last tier (highest tier)
        last_tier = sorted_tiers[-1]
        return {
            "charge": float(last_tier.charge),
            "minCartValue": get_max_amount(last_tier) if get_max_amount(last_tier) != float("inf") else 0,
            "tier": last_tier,
        }

    async def create(self, charge_data: DeliveryChargeInternalCreate) -> DeliveryChargeInternal:
        # Check if pincode already exists
        if charge_data.pincode:
            existing = await self.findByPincode(charge_data.pincode)
            if existing:
                raise ValueError("Pincode already exists")

        # Generate unique ID for state-district-city combination (for backward compatibility)
        all_charges = await self.storage.findAll()
        max_id = 0
        for charge in all_charges:
            if charge.locationId and isinstance(charge.locationId, int):
                max_id = max(max_id, charge.locationId)
        location_id = max_id + 1

        apply_default = charge_data.applyDefaultCharge

        charge_internal = DeliveryChargeInternalCreate(
            locationId=location_id,
            pincode=charge_data.pincode or None,
            state=charge_data.state,
            city=charge_data.city,
            district=charge_data.district,
            applyDefaultCharge=apply_default,
            charge=None if apply_default else (float(charge_data.charge) if charge_data.charge is not None else None),
            minCartValue=None if apply_default else (float(charge_data.minCartValue) if charge_data.minCartValue is not None else None),
            tiers=None if apply_default else charge_data.tiers,
            serviceableForCustomer=charge_data.serviceableForCustomer is True,
            serviceableForWholesaler=charge_data.serviceableForWholesaler is True,
            isActive=charge_data.isActive,
            description=charge_data.description,
            urgentDeliveryAvailable=False,
            urgentDeliveryCharge=float(charge_data.urgentDeliveryCharge) if charge_data.urgentDeliveryCharge is not None else None,
        )

        return await self.storage.create(charge_internal)

    async def update(self, id: str, update_data: DeliveryChargeInternalUpdate) -> DeliveryChargeInternal:
        if update_data.charge is not None:
            update_data.charge = float(update_data.charge)
        if update_data.minCartValue is not None:
            update_data.minCartValue = float(update_data.minCartValue)
        if update_data.urgentDeliveryCharge is not None:
            update_data.urgentDeliveryCharge = float(update_data.urgentDeliveryCharge)
        # Update role applicability if provided
        if update_data.applicableToWholesaler is not None:
            update_data.applicableToWholesaler = bool(update_data.applicableToWholesaler)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)

    async def findByPinCode(self, zip_code: str):
        """Find delivery charge by pin code. If no delivery charge has been added by super admin, return None (will default to 0)"""
        # The system uses location-based charges (state, city, district), not zipCode-based
        # So we return default charge or None to use 0

        # Try to get default charge
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.isActive:
            return {"charge": default_charge.defaultCharge, "isActive": True}

        # If no default charge, return None (will be treated as 0 in order creation)
        return None


delivery_charge_repository = DeliveryChargeRepository()


