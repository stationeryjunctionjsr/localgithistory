with open('app/routers/cart.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_dict = '''            cart_items.append(
                {
                    "_id": item.id,
                    "product": {
                        "_id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "images": product.images,
                        "mrp": product.mrp,
                        "mrpPerCase": product.mrp_per_case,
                        "quantityPerCase": product.quantity_per_case,
                        "price": price,
                    },
                    "quantity": quantity,
                    "sellAsCase": sell_as_case,
                    "price": price,
                    "subtotal": subtotal,
                    "outOfStock": is_out_of_stock,
                }
            )'''

new_dict = '''            cart_items.append(
                {
                    "_id": item.id,
                    "productId": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "images": product.images,
                    "mrp": product.mrp,
                    "mrpPerCase": product.mrp_per_case,
                    "quantityPerCase": product.quantity_per_case,
                    "quantity": quantity,
                    "sellAsCase": sell_as_case,
                    "price": price,
                    "subtotal": subtotal,
                    "outOfStock": is_out_of_stock,
                    "bundleId": item.bundleId,
                    "bundleName": item.bundleName,
                    "variantAttributes": item.variantAttributes,
                }
            )'''

if old_dict in text:
    text = text.replace(old_dict, new_dict)
else:
    print("Could not find dict to replace")

with open('app/routers/cart.py', 'w', encoding='utf-8') as f:
    f.write(text)
