import re

with open('backend/app/repositories/product_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace dict instantiation + **kwargs with direct instantiation for create
create_block = '''        product = {
            "productId": product_id,
            "productIdFormatted": product_id_formatted,
            "name": data_dict["name"],
            "description": data_dict.get("description", ""),
            "sku": sku_val,
            "categoryId": data_dict["categoryId"],
            "subCategoryId": data_dict.get("subCategoryId"),
            "brandId": data_dict.get("brandId"),
            "price": float(data_dict.get("price") if data_dict.get("price") is not None else 0),
            "mrp": float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
            "stock": int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
            "unit": data_dict.get("unit", "pc"),
            "isActive": data_dict.get("isActive", True),
            "tags": data_dict.get("tags", []),
            "images": data_dict.get("images", []),
            "thumbnail": data_dict.get("thumbnail"),
            "variants": data_dict.get("variantCombinations", []),
            "details": data_dict.get("details", {}),
        }

        # Check for duplicate variants
        if product.get("variants"):
            existing_skus = set()
            for combo in product["variants"]:
                if "sku" not in combo or not combo["sku"]:
                    combo["sku"] = (
                        f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
                    )
                if combo["sku"] in existing_skus:
                    raise ValueError(f"Duplicate variant SKU generated or provided: {combo['sku']}")
                existing_skus.add(combo["sku"])

        internal_create = ProductInternalCreate(**product)
        created = await self.storage.create(internal_create)'''

new_create_block = '''        internal_create = ProductInternalCreate(
            productId=product_id,
            productIdFormatted=product_id_formatted,
            name=data_dict["name"],
            description=data_dict.get("description", ""),
            sku=sku_val,
            categoryId=data_dict["categoryId"],
            subCategoryId=data_dict.get("subCategoryId"),
            brandId=data_dict.get("brandId"),
            price=float(data_dict.get("price") if data_dict.get("price") is not None else 0),
            mrp=float(data_dict.get("mrp") if data_dict.get("mrp") is not None else 0),
            stock=int(data_dict.get("stock") if data_dict.get("stock") is not None else 0),
            unit=data_dict.get("unit", "pc"),
            isActive=data_dict.get("isActive", True),
            tags=data_dict.get("tags", []),
            images=data_dict.get("images", []),
            thumbnail=data_dict.get("thumbnail"),
            variants=data_dict.get("variantCombinations", []),
            details=data_dict.get("details", {}),
        )

        if internal_create.variants:
            existing_skus = set()
            for combo in internal_create.variants:
                if "sku" not in combo or not combo["sku"]:
                    combo["sku"] = (
                        f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
                    )
                if combo["sku"] in existing_skus:
                    raise ValueError(f"Duplicate variant SKU generated or provided: {combo['sku']}")
                existing_skus.add(combo["sku"])

        created = await self.storage.create(internal_create)'''

content = content.replace(create_block, new_create_block)

# Replace internal_update = ProductInternalUpdate(**data_dict) with just instantiating it normally, but data_dict might have extra keys.
update_block = '''        internal_update = ProductInternalUpdate(**data_dict)
        updated = await self.storage.update(id, internal_update)'''

new_update_block = '''        internal_update = ProductInternalUpdate.model_validate(data_dict)
        updated = await self.storage.update(id, internal_update)'''
content = content.replace(update_block, new_update_block)

with open('backend/app/repositories/product_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
