from typing import TYPE_CHECKING, Optional, List, Union
from app.models.daos_flat import (
    DeliveryChargeInternal,
    DeliveryChargeDefaultInternal,
    DeliveryChargeInternalCreate,
    DeliveryChargeInternalUpdate,
    DeliveryChargeDefaultInternalCreate,
    DeliveryChargeDefaultInternalUpdate,
    DeliveryChargeTierInternal,
    DeliveryZoneInternal,
)
from app.models.schemas import DeliveryFeeCalculationResult
from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import DeliveryChargeInternal


class DeliveryChargeRepository:
    def __init__(self):
        self.storage = get_storage("deliveryCharges")
        self.default_storage = get_storage("deliveryChargeDefaults")
        self.zone_storage = get_storage("deliveryZones")

    async def findAll(self, query: Optional[dict] = None) -> list[DeliveryChargeInternal]:
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findByLocation(self, state: str, city: str, district: str):
        return await self.storage.findByLocation(state=state, district=district, city=city)

    async def findByPincode(self, pincode: str):
        """Find pincode-specific charge"""
        return await self.storage.findByPincode(pincode)

    async def isPincodeServiceable(self, pincode: str, user_role: str) -> bool:
        """Check if a pincode is serviceable for a user role"""
        # If pincode is not added, it's not serviceable
        charge = await self.findByPincode(pincode)
        if not charge:
            return False

        # Check serviceability based on user role
        if user_role == "customer" or not user_role:
            return charge.serviceable_for_customer is True
        elif user_role == "wholesaler":
            return charge.serviceable_for_wholesaler is True
        # All other roles (e.g. customer) use customer serviceability
        return charge.serviceable_for_customer is True

    async def getDefaultCharge(self) -> Optional[DeliveryChargeDefaultInternal]:
        return await self.default_storage.getDefault()

    async def setdefault_charge(self, default_data: DeliveryChargeDefaultInternalCreate) -> DeliveryChargeDefaultInternal:
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
            applicableToWholesaler=default_data.applicable_to_wholesaler,
            is_active=default_data.is_active,
            tiers=tiers_internal
        )

        if existing:
            return await self.default_storage.update(existing.id, default_charge)
        else:
            default_create = DeliveryChargeDefaultInternalCreate(
                applicableToWholesaler=default_data.applicable_to_wholesaler,
                is_active=default_data.is_active,
                tiers=tiers_internal
            )
            return await self.default_storage.create(default_create)

    async def deletedefault_charge(self):
        """Delete the default delivery charge"""
        existing = await self.getDefaultCharge()
        if not existing:
            return None
        return await self.default_storage.delete(existing.id)

    async def getHyperlocalChargeForZone(
        self,
        zone_id: Union[int, str],
        order_amount: float,
        user_role: str = "customer",
    ) -> DeliveryFeeCalculationResult:
        """Calculate delivery fee for a zone in Hyperlocal mode.
        - Wholesalers: Checked against zone customer_type and applicable_to_wholesaler.
        - If zone.apply_default_charge == True: Falls back to global hyperlocal defaults.
        - If zone.apply_default_charge == False: Uses zone custom tiers or zone flat charge.
        """
        zone = await self.zone_storage.findById(zone_id)
        if not zone or not zone.is_active:
            return DeliveryFeeCalculationResult(charge=0.0, min_cart_value=0.0, is_free_delivery=True, source="none")

        is_wholesaler = (user_role == "wholesaler")
        if is_wholesaler and zone.customer_type not in ("business", "both"):
            return DeliveryFeeCalculationResult(charge=0.0, min_cart_value=0.0, is_free_delivery=True, source="exempt")

        default_charge = await self.getDefaultCharge()
        if is_wholesaler and default_charge and default_charge.applicable_to_wholesaler is False:
            return DeliveryFeeCalculationResult(charge=0.0, min_cart_value=0.0, is_free_delivery=True, source="exempt")

        # 1. Global hyperlocal fallback
        if zone.apply_default_charge:
            base_charge = float(default_charge.hyperlocal_base_charge) if default_charge and default_charge.hyperlocal_base_charge is not None else 40.0
            free_threshold = float(default_charge.hyperlocal_free_threshold) if default_charge and default_charge.hyperlocal_free_threshold is not None else 300.0
            urgent_charge = float(default_charge.hyperlocal_urgent_delivery_charge) if default_charge and default_charge.hyperlocal_urgent_delivery_charge is not None else 50.0
            urgent_avail = bool(zone.urgent_delivery_available) if zone.urgent_delivery_available is not None else False

            is_free = (order_amount >= free_threshold) if free_threshold > 0 else False
            fee = 0.0 if is_free else base_charge
            return DeliveryFeeCalculationResult(
                charge=fee,
                min_cart_value=free_threshold,
                is_free_delivery=is_free,
                source="hyperlocal_default",
                delivery_charge=base_charge,
                urgent_delivery_available=urgent_avail,
                urgent_delivery_charge=urgent_charge,
            )

        # 2. Zone custom tiers
        if zone.tiers and len(zone.tiers) > 0:
            sorted_tiers = sorted(zone.tiers, key=lambda t: float(t.min if t.min is not None else 0.0))
            applicable_tier = None
            for tier in sorted_tiers:
                tier_min = float(tier.min if tier.min is not None else 0.0)
                tier_max = float(tier.max if tier.max is not None and tier.max != float("inf") else float("inf"))
                if tier_min <= order_amount < tier_max:
                    applicable_tier = tier
                    break
            if not applicable_tier:
                applicable_tier = sorted_tiers[-1]

            tier_charge = float(applicable_tier.charge if applicable_tier.charge is not None else 0.0)
            tier_max_val = float(applicable_tier.max if applicable_tier.max is not None and applicable_tier.max != float("inf") else 0.0)
            return DeliveryFeeCalculationResult(
                charge=tier_charge,
                min_cart_value=tier_max_val,
                is_free_delivery=(tier_charge == 0.0),
                source="zone_tier",
                delivery_charge=tier_charge,
                applied_tier_min=float(applicable_tier.min or 0.0),
                applied_tier_max=float(applicable_tier.max) if applicable_tier.max is not None and applicable_tier.max != float("inf") else None,
                applied_tier_charge=tier_charge,
                urgent_delivery_available=bool(zone.urgent_delivery_available) if zone.urgent_delivery_available is not None else False,
                urgent_delivery_charge=float(zone.urgent_delivery_charge) if zone.urgent_delivery_charge is not None else None,
            )

        # 3. Flat zone custom charge
        base_charge = float(zone.delivery_charge) if zone.delivery_charge is not None else 0.0
        free_threshold = float(zone.min_cart_value) if zone.min_cart_value is not None else 0.0
        urgent_charge = float(zone.urgent_delivery_charge) if zone.urgent_delivery_charge is not None else None
        urgent_avail = bool(zone.urgent_delivery_available) if zone.urgent_delivery_available is not None else False
        is_free = (order_amount >= free_threshold) if free_threshold > 0 else False
        fee = 0.0 if is_free else base_charge

        return DeliveryFeeCalculationResult(
            charge=fee,
            min_cart_value=free_threshold,
            is_free_delivery=is_free,
            source="zone_custom",
            delivery_charge=base_charge,
            urgent_delivery_available=urgent_avail,
            urgent_delivery_charge=urgent_charge,
        )

    async def getCourierCharge(
        self,
        order_amount: float,
        user_role: str = "customer",
    ) -> DeliveryFeeCalculationResult:
        """Calculate courier shipping fee for Pan-India mode.
        Uses courier_base_charge and courier_free_threshold from global defaults.
        """
        default_charge = await self.getDefaultCharge()
        is_wholesaler = (user_role == "wholesaler")
        if is_wholesaler and default_charge and default_charge.applicable_to_wholesaler is False:
            return DeliveryFeeCalculationResult(charge=0.0, min_cart_value=0.0, is_free_delivery=True, source="exempt")

        courier_base = float(default_charge.courier_base_charge) if default_charge and default_charge.courier_base_charge is not None else 70.0
        courier_threshold = float(default_charge.courier_free_threshold) if default_charge and default_charge.courier_free_threshold is not None else 1500.0
        is_free = (order_amount >= courier_threshold) if courier_threshold > 0 else False
        fee = 0.0 if is_free else courier_base

        return DeliveryFeeCalculationResult(
            charge=fee,
            min_cart_value=courier_threshold,
            is_free_delivery=is_free,
            source="courier",
            delivery_charge=courier_base,
            urgent_delivery_available=False,
            urgent_delivery_charge=None,
        )

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
            if pincode_charge.apply_default_charge:
                default_charge = await self.getDefaultCharge()

                urgent_charge = None
                urgent_avail = False
                if default_charge:
                    urgent_charge = default_charge.urgent_delivery_charge
                    # urgent_avail = default_charge.urgent_delivery_available
                    urgent_avail = False

                if default_charge and default_charge.is_active:
                    is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
                    if not is_applicable:
                        from app.routers.delivery_charges import LocationChargeResponse
                        return LocationChargeResponse(
                            charge=0,
                            min_cart_value=0,
                            source="pincode-default",
                            delivery_charge=default_charge.charge if default_charge else None,
                            isApplicableToRole=False,
                            urgentDeliveryAvailable=urgent_avail,
                            urgent_delivery_charge=urgent_charge,
                        )

                    if default_charge.tiers and len(default_charge.tiers) > 0:
                        tier_charge = self.calculateTieredCharge(default_charge.tiers, order_amount)
                        from app.routers.delivery_charges import LocationChargeResponse
                        return LocationChargeResponse(
                            charge=tier_charge["charge"],
                            min_cart_value=tier_charge["min_cart_value"],
                            source="pincode-default-tiered",
                            delivery_charge=default_charge.charge if default_charge else None,
                            isApplicableToRole=True,
                            appliedTier=tier_charge["tier"],
                            urgentDeliveryAvailable=urgent_avail,
                            urgent_delivery_charge=urgent_charge,
                        )

                    from app.routers.delivery_charges import LocationChargeResponse
                    return LocationChargeResponse(
                        charge=0,
                        min_cart_value=0,
                        source="pincode-default-no-tiers",
                        delivery_charge=default_charge.charge if default_charge else None,
                        isApplicableToRole=True,
                        urgentDeliveryAvailable=urgent_avail,
                        urgent_delivery_charge=urgent_charge,
                    )
            else:
                # urgent_avail = pincode_charge.urgent_delivery_available
                urgent_avail = False
                # Use pincode-specific tiers or charge
                if pincode_charge.tiers and len(pincode_charge.tiers) > 0:
                    tier_charge = self.calculateTieredCharge(pincode_charge.tiers, order_amount)
                    from app.routers.delivery_charges import LocationChargeResponse
                    return LocationChargeResponse(
                        charge=tier_charge["charge"],
                        min_cart_value=tier_charge["min_cart_value"],
                        source="pincode-tiered",
                        delivery_charge=pincode_charge.charge if pincode_charge else None,
                        isApplicableToRole=True,
                        appliedTier=tier_charge["tier"],
                        urgentDeliveryAvailable=urgent_avail,
                        urgent_delivery_charge=pincode_charge.urgent_delivery_charge,
                    )
                else:
                    from app.routers.delivery_charges import LocationChargeResponse
                    return LocationChargeResponse(
                        charge=pincode_charge.charge or 0,
                        min_cart_value=pincode_charge.min_cart_value or 0,
                        source="pincode",
                        delivery_charge=pincode_charge.charge if pincode_charge else None,
                        isApplicableToRole=True,
                        urgentDeliveryAvailable=urgent_avail,
                        urgent_delivery_charge=pincode_charge.urgent_delivery_charge,
                    )

        # Fallback to city-specific charge (for backward compatibility)
        city_charge = await self.findByLocation(state, city, district)

        if city_charge:
            # Check role applicability for city-specific charge
            is_applicable = self.isChargeApplicableToRole(city_charge, user_role)
            # urgent_avail = city_charge.urgent_delivery_available
            urgent_avail = False

            from app.routers.delivery_charges import LocationChargeResponse
            return LocationChargeResponse(
                charge=city_charge.charge if is_applicable else 0,
                min_cart_value=city_charge.min_cart_value or 0,
                source="city",
                delivery_charge=city_charge.charge if city_charge else None,
                isApplicableToRole=is_applicable,
                urgentDeliveryAvailable=urgent_avail,
                urgent_delivery_charge=city_charge.urgent_delivery_charge,
            )

        # Use default if available
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.is_active:
            is_applicable = self.isChargeApplicableToRole(default_charge, user_role)
            # urgent_avail = default_charge.urgent_delivery_available
            urgent_avail = False
            urgent_charge = default_charge.urgent_delivery_charge
            
            if not is_applicable:
                from app.routers.delivery_charges import LocationChargeResponse
                return LocationChargeResponse(
                    charge=0,
                    min_cart_value=0,
                    source="default",
                    delivery_charge=default_charge.charge if default_charge else None,
                    isApplicableToRole=False,
                    urgentDeliveryAvailable=urgent_avail,
                    urgent_delivery_charge=urgent_charge,
                )

            # Default charges are always tiered (no single charge fallback)
            if default_charge.tiers and len(default_charge.tiers) > 0:
                tier_charge = self.calculateTieredCharge(default_charge.tiers, order_amount)
                from app.routers.delivery_charges import LocationChargeResponse
                return LocationChargeResponse(
                    charge=tier_charge["charge"],
                    min_cart_value=tier_charge["min_cart_value"],
                    source="default-tiered",
                    delivery_charge=default_charge.charge if default_charge else None,
                    isApplicableToRole=True,
                    appliedTier=tier_charge["tier"],
                    urgentDeliveryAvailable=urgent_avail,
                    urgent_delivery_charge=urgent_charge,
                )

            # If no tiers configured, no delivery charge
            from app.routers.delivery_charges import LocationChargeResponse
            return LocationChargeResponse(
                charge=0,
                min_cart_value=0,
                source="default-no-tiers",
                delivery_charge=default_charge.charge if default_charge else None,
                isApplicableToRole=True,
                urgentDeliveryAvailable=urgent_avail,
                urgent_delivery_charge=urgent_charge,
            )

        from app.routers.delivery_charges import LocationChargeResponse
        return LocationChargeResponse(
            charge=0,
            min_cart_value=0,
            source="none",
            delivery_charge=None,
            isApplicableToRole=True,
            urgentDeliveryAvailable=False,
            urgent_delivery_charge=None,
        )

    def isChargeApplicableToRole(self, charge_data: 'DeliveryChargeInternal', user_role: str) -> bool:
        """Check if delivery charge is applicable to the user's role"""
        if not charge_data:
            return True  # Default to applicable if no data

        # For customers, always applicable
        if user_role == "customer" or not user_role:
            return True

        # For wholesalers
        if user_role == "wholesaler":
            return charge_data.applicable_to_wholesaler  # Default to true if not specified

        return True

    def calculateTieredCharge(self, tiers: list, order_amount: float) -> dict:
        """Calculate delivery charge based on tiered structure"""
        if not tiers or len(tiers) == 0:
            return {"charge": 0, "min_cart_value": 0, "tier": None}

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
                    "min_cart_value": max_amount if max_amount != float("inf") else 0,
                    "tier": tier,
                }

        # If no tier found, return the last tier (highest tier)
        last_tier = sorted_tiers[-1]
        return {
            "charge": float(last_tier.charge),
            "min_cart_value": get_max_amount(last_tier) if get_max_amount(last_tier) != float("inf") else 0,
            "tier": last_tier,
        }

    async def create(self, charge_data: DeliveryChargeInternalCreate) -> DeliveryChargeInternal:
        # Check if pincode already exists
        if charge_data.pincode:
            existing = await self.findByPincode(charge_data.pincode)
            if existing:
                raise ValueError("Pincode already exists")

        # Generate unique ID for state-district-city combination via direct SQL MAX
        location_id = await self.storage.getMaxLocationId() + 1

        apply_default = charge_data.apply_default_charge

        charge_internal = DeliveryChargeInternalCreate(
            location_id=location_id,
            pincode=charge_data.pincode or None,
            state=charge_data.state,
            city=charge_data.city,
            district=charge_data.district,
            apply_default_charge=apply_default,
            charge=None if apply_default else (float(charge_data.charge) if charge_data.charge is not None else None),
            min_cart_value=None if apply_default else (float(charge_data.min_cart_value) if charge_data.min_cart_value is not None else None),
            tiers=None if apply_default else charge_data.tiers,
            serviceable_for_customer=charge_data.serviceable_for_customer is True,
            serviceable_for_wholesaler=charge_data.serviceable_for_wholesaler is True,
            is_active=charge_data.is_active,
            description=charge_data.description,
            urgent_delivery_available=False,
            urgent_delivery_charge=float(charge_data.urgent_delivery_charge) if charge_data.urgent_delivery_charge is not None else None,
        )

        return await self.storage.create(charge_internal)

    async def update(self, id: str, update_data: DeliveryChargeInternalUpdate) -> DeliveryChargeInternal:
        if update_data.charge is not None:
            update_data.charge = float(update_data.charge)
        if update_data.min_cart_value is not None:
            update_data.min_cart_value = float(update_data.min_cart_value)
        if update_data.urgent_delivery_charge is not None:
            update_data.urgent_delivery_charge = float(update_data.urgent_delivery_charge)
        # Update role applicability if provided
        if update_data.applicable_to_wholesaler is not None:
            update_data.applicable_to_wholesaler = bool(update_data.applicable_to_wholesaler)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)

    async def findByPinCode(self, zip_code: str):
        """Find delivery charge by pin code. If no delivery charge has been added by super admin, return None (will default to 0)"""
        # The system uses location-based charges (state, city, district), not zipCode-based
        # So we return default charge or None to use 0

        # Try to get default charge
        default_charge = await self.getDefaultCharge()
        if default_charge and default_charge.is_active:
            return {"charge": default_charge.default_charge, "is_active": True}

        # If no default charge, return None (will be treated as 0 in order creation)
        return None

    async def isPanIndiaServiceable(self, pincode: str) -> bool:
        """
        Check if a pincode is serviceable via standard 3PL Pan-India courier.
        A pincode is serviceable if:
        1. It is a valid 6-digit Indian PIN code (digits only, starting with 1-9).
        2. If explicitly configured in sj_delivery_charges, serviceable_for_customer is not False.
        """
        if not pincode or len(pincode) != 6 or not pincode.isdigit() or pincode[0] == "0":
            return False

        try:
            charge = await self.findByPincode(pincode)
            if charge and charge.serviceable_for_customer is False and not charge.is_active:
                return False
        except Exception:
            pass
        return True


delivery_charge_repository = DeliveryChargeRepository()


