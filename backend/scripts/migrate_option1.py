import asyncio
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.database import get_async_session_factory
from sqlalchemy import text


def _safe_float(v):
    try:
        return float(v) if v is not None else 0.0
    except:
        return 0.0


def _parse_datetime(v):
    if not v:
        return None
    # Remove 'Z' if present and convert to MySQL datetime format string
    return v.replace("Z", "").replace("T", " ")


async def run_migration():
    factory = get_async_session_factory()
    if not factory:
        print("Could not get database session factory.")
        return

    print("Starting data migration for Option 1 (Normalization)...")

    async with factory() as session:
        # ==========================================
        # 0. Execute DDL from migrate_option1.sql
        # ==========================================
        print("Executing DDL from migrate_option1.sql...")
        sql_path = os.path.join(os.path.dirname(__file__), "migrate_option1.sql")
        if os.path.exists(sql_path):
            with open(sql_path, "r") as f:
                sql_content = f.read()
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            for stmt in statements:
                if not stmt.startswith("--"):
                    try:
                        await session.execute(text(stmt))
                    except Exception as e:
                        if "Duplicate column name" in str(e) or "Table 'sj_sub_order_items' already exists" in str(e):
                            pass  # Ignore if already ran
                        else:
                            print(f"Warning executing DDL: {e}")
        else:
            print(f"Warning: {sql_path} not found. Skipping DDL.")

        await session.commit()
        print("DDL execution finished.")

        # ==========================================
        # 1. Migrate sj_seller_availability
        # ==========================================
        print("Migrating sj_seller_availability...")
        sa_result = await session.execute(text("SELECT id, doc FROM sj_seller_availability WHERE doc IS NOT NULL"))
        sa_rows = sa_result.fetchall()

        sa_update_sql = text("""
            UPDATE sj_seller_availability
            SET reason = :reason, created_by = :created_by, cancelled_at = :cancelled_at
            WHERE id = :id
        """)

        sa_count = 0
        for row in sa_rows:
            try:
                doc = json.loads(row.doc) if isinstance(row.doc, str) else row.doc
                await session.execute(
                    sa_update_sql,
                    {
                        "id": row.id,
                        "reason": doc.get("reason"),
                        "created_by": doc.get("createdBy"),
                        "cancelled_at": _parse_datetime(doc.get("cancelledAt")),
                    },
                )
                sa_count += 1
            except Exception as e:
                print(f"Error processing seller_availability {row.id}: {e}")

        print(f"Migrated {sa_count} seller availability records.")

        # ==========================================
        # 2. Migrate sj_sub_orders
        # ==========================================
        print("Migrating sj_sub_orders...")
        so_result = await session.execute(text("SELECT id, doc FROM sj_sub_orders WHERE doc IS NOT NULL"))
        so_rows = so_result.fetchall()

        so_update_sql = text("""
            UPDATE sj_sub_orders SET
                sub_order_number = :sub_order_number,
                parent_order_number = :parent_order_number,
                seller_name = :seller_name,
                subtotal = :subtotal,
                tax = :tax,
                shipping = :shipping,
                delivery_gst = :delivery_gst,
                discount = :discount,
                order_type = :order_type,
                payment_method = :payment_method,
                is_urgent_delivery = :is_urgent_delivery,
                delivery_slot_config_id = :delivery_slot_config_id,
                delivery_slot_id = :delivery_slot_id,
                delivery_slot_date = :delivery_slot_date,
                notes = :notes,
                coupon_code = :coupon_code,
                coupon_info_type = :coupon_info_type,
                coupon_info_value = :coupon_info_value,
                shipping_name = :shipping_name,
                shipping_phone = :shipping_phone,
                shipping_line1 = :shipping_line1,
                shipping_city = :shipping_city,
                shipping_state = :shipping_state,
                shipping_pincode = :shipping_pincode,
                billing_name = :billing_name,
                billing_phone = :billing_phone,
                billing_line1 = :billing_line1,
                billing_city = :billing_city,
                billing_state = :billing_state,
                billing_pincode = :billing_pincode,
                delivered_at = :delivered_at,
                dispatched_at = :dispatched_at,
                cancelled_at = :cancelled_at
            WHERE id = :id
        """)

        item_insert_sql = text("""
            INSERT INTO sj_sub_order_items (sub_order_id, product_id, name, qty, price)
            VALUES (:sub_order_id, :product_id, :name, :qty, :price)
        """)

        so_count = 0
        items_count = 0

        # Clear existing items to ensure idempotency
        await session.execute(text("DELETE FROM sj_sub_order_items"))

        for row in so_rows:
            try:
                doc = json.loads(row.doc) if isinstance(row.doc, str) else row.doc

                # Extract embedded objects
                slot = doc.get("deliverySlot") or {}
                c_info = doc.get("couponInfo") or {}
                s_addr = doc.get("shippingAddress") or {}
                b_addr = doc.get("billingAddress") or {}

                await session.execute(
                    so_update_sql,
                    {
                        "id": row.id,
                        "sub_order_number": doc.get("subOrderNumber"),
                        "parent_order_number": doc.get("parentOrderNumber"),
                        "seller_name": doc.get("sellerName"),
                        "subtotal": _safe_float(doc.get("subtotal")),
                        "tax": _safe_float(doc.get("tax")),
                        "shipping": _safe_float(doc.get("shipping")),
                        "delivery_gst": _safe_float(doc.get("deliveryGst")),
                        "discount": _safe_float(doc.get("discount")),
                        "order_type": doc.get("orderType"),
                        "payment_method": doc.get("paymentMethod"),
                        "is_urgent_delivery": 1 if doc.get("isUrgentDelivery") else 0,
                        "delivery_slot_config_id": slot.get("configId"),
                        "delivery_slot_id": slot.get("slotId"),
                        "delivery_slot_date": slot.get("date"),
                        "notes": doc.get("notes"),
                        "coupon_code": doc.get("couponCode"),
                        "coupon_info_type": c_info.get("discountType"),
                        "coupon_info_value": _safe_float(c_info.get("discountValue")),
                        "shipping_name": s_addr.get("name"),
                        "shipping_phone": s_addr.get("phone"),
                        "shipping_line1": s_addr.get("line1"),
                        "shipping_city": s_addr.get("city"),
                        "shipping_state": s_addr.get("state"),
                        "shipping_pincode": s_addr.get("pincode"),
                        "billing_name": b_addr.get("name"),
                        "billing_phone": b_addr.get("phone"),
                        "billing_line1": b_addr.get("line1"),
                        "billing_city": b_addr.get("city"),
                        "billing_state": b_addr.get("state"),
                        "billing_pincode": b_addr.get("pincode"),
                        "delivered_at": _parse_datetime(doc.get("deliveredAt")),
                        "dispatched_at": _parse_datetime(doc.get("dispatchedAt")),
                        "cancelled_at": _parse_datetime(doc.get("cancelledAt")),
                    },
                )
                so_count += 1

                # Insert items
                items = doc.get("items", [])
                for item in items:
                    await session.execute(
                        item_insert_sql,
                        {
                            "sub_order_id": row.id,
                            "product_id": item.get("productId", ""),
                            "name": item.get("name", ""),
                            "qty": int(item.get("qty") or 0),
                            "price": _safe_float(item.get("price")),
                        },
                    )
                    items_count += 1

            except Exception as e:
                print(f"Error processing sub_order {row.id}: {e}")

        print(f"Migrated {so_count} sub_orders and {items_count} items.")

        # ==========================================
        # 3. Drop doc columns
        # ==========================================
        print("Dropping 'doc' columns from sj_seller_availability and sj_sub_orders...")
        try:
            await session.execute(text("ALTER TABLE sj_seller_availability DROP COLUMN doc"))
            print("Dropped 'doc' from sj_seller_availability.")
        except Exception as e:
            print(f"Warning: Could not drop 'doc' from sj_seller_availability (might already be dropped): {e}")

        try:
            await session.execute(text("ALTER TABLE sj_sub_orders DROP COLUMN doc"))
            print("Dropped 'doc' from sj_sub_orders.")
        except Exception as e:
            print(f"Warning: Could not drop 'doc' from sj_sub_orders (might already be dropped): {e}")

        await session.commit()
        print("Data migration complete!")


if __name__ == "__main__":
    asyncio.run(run_migration())
