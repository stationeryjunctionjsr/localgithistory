"""
Product Variations Utility
Helper functions for managing product variations
"""

from typing import Dict, List, Optional


def validate_variation(variation: Dict) -> bool:
    """Validate variation structure"""
    if not (variation["name"] if "name" in variation else None) or not (variation["type"] if "type" in variation else None):
        raise ValueError("Variation must have name and type")

    options = (variation["options"] if "options" in variation else [])
    if not isinstance(options, list) or len(options) == 0:
        raise ValueError("Variation must have at least one option")

    # Validate each option
    for index, option in enumerate(options):
        if not (option["value"] if "value" in option else None):
            raise ValueError(f"Option {index + 1} must have a value")
        if "priceModifier" not in option:
            option["priceModifier"] = 0
        if "stock" not in option:
            option["stock"] = 0

    return True


def validate_variations(variations: Optional[List[Dict]]) -> bool:
    """Validate all variations for a product"""
    if not variations or not isinstance(variations, list):
        return True  # Variations are optional

    for index, variation in enumerate(variations):
        try:
            validate_variation(variation)
        except ValueError as e:
            raise ValueError(f"Variation {index + 1}: {str(e)}")

    return True


def calculate_price_with_variations(base_price: float, selected_variations: Optional[Dict] = None) -> float:
    """Calculate price with variation modifiers"""
    if not selected_variations:
        return base_price

    final_price = base_price

    for option in selected_variations.values():
        if option and "priceModifier" in option:
            final_price += (option["priceModifier"] if "priceModifier" in option else 0)

    return max(0, final_price)  # Ensure price is not negative


def get_stock_for_variations(product: Dict, selected_variations: Optional[Dict] = None) -> int:
    """Get stock for specific variation combination"""
    if not (product["variations"] if "variations" in product else None) or len((product["variations"] if "variations" in product else [])) == 0:
        return (product["stock"] if "stock" in product else 0)

    # If variations are selected, check stock for that combination
    min_stock = float("inf")

    for variation in (product["variations"] if "variations" in product else []):
        selected_option = (selected_variations[variation["name"]] if "name" in variation and variation["name"] in selected_variations else None) if selected_variations else None
        if selected_option and "stock" in selected_option:
            min_stock = min(min_stock, (selected_option["stock"] if "stock" in selected_option else 0))

    return int(min_stock) if min_stock != float("inf") else (product["stock"] if "stock" in product else 0)


def get_all_variation_combinations(product: Dict) -> List[Dict]:
    """Get all possible variation combinations"""
    variations = (product["variations"] if "variations" in product else [])
    if not variations or len(variations) == 0:
        return [{}]  # No variations, one combination

    combinations = []

    def generate_combinations(index: int, current: Dict):
        if index >= len(variations):
            combinations.append(current.copy())
            return

        variation = variations[index]
        for option in (variation["options"] if "options" in variation else []):
            new_current = current.copy()
            new_current[(variation["name"] if "name" in variation else None)] = option
            generate_combinations(index + 1, new_current)

    generate_combinations(0, {})
    return combinations
