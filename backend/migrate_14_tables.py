import asyncio

import aiomysql

DB_URLS = {
    "sjqadb": {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjqadb",
    },
    "sjuatdb": {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjuatdb",
    },
}

# Config for the 14 remaining tables
# For each table, define its child tables and the properties they map to.
# child_tables: API key -> (child_table_name, [columns_in_db], [columns_in_api], is_flat_list, is_key_value)
TABLES_CONFIG = {
    "sj_activities": {
        "api_name": "activities",
        "scalar_map": {"meta": "meta"},  # we drop 'meta' from scalar and make child
        "child_tables": {"meta": ("sj_activity_meta", ["meta_key", "meta_value"], ["key", "value"], False, True)},
    },
    "sj_notifications": {
        "api_name": "notifications",
        "child_tables": {"data": ("sj_notification_data", ["data_key", "data_value"], ["key", "value"], False, True)},
    },
    "sj_return_requests": {
        "api_name": "returnRequests",
        "child_tables": {
            "items": (
                "sj_return_request_items",
                ["product_id", "quantity", "reason"],
                ["productId", "quantity", "reason"],
                False,
                False,
            ),
            "valetDeclineHistory": (
                "sj_return_valet_declines",
                ["valet_id", "reason"],
                ["valetId", "reason"],
                False,
                False,
            ),
        },
    },
    "sj_schemes": {
        "api_name": "schemes",
        "child_tables": {"applicableRoles": ("sj_scheme_roles", ["role"], [""], True, False)},
    },
    "sj_contacts": {
        "api_name": "contacts",
        "child_tables": {
            "addresses": ("sj_contact_addresses", ["address"], [""], True, False),
            "phoneNumbers": ("sj_contact_phones", ["phone"], [""], True, False),
        },
    },
    "sj_support_tickets": {
        "api_name": "supportTickets",
        "child_tables": {
            "attachments": ("sj_ticket_attachments", ["url"], [""], True, False),
            "responses": ("sj_ticket_responses", ["admin_id", "message"], ["adminId", "message"], False, False),
        },
    },
    "sj_device_subscriptions": {
        "api_name": "deviceSubscriptions",
        "child_tables": {
            "keys": ("sj_device_keys", ["key_name", "key_value"], ["key", "value"], False, True),
            "subscription": ("sj_device_sub_data", ["sub_key", "sub_val"], ["key", "value"], False, True),
        },
    },
    "sj_collections": {
        "api_name": "collections",
        "child_tables": {
            "visiblePages": ("sj_collection_pages", ["page"], [""], True, False),
            "userSegments": ("sj_collection_segments", ["segment"], [""], True, False),
            "visibilityRules": ("sj_collection_rules", ["rule"], [""], True, False),
            "productIds": ("sj_collection_products", ["product_id"], [""], True, False),
        },
    },
    "sj_search_tags": {
        "api_name": "searchTags",
        "child_tables": {
            "categories": ("sj_search_tag_categories", ["category"], [""], True, False),
            "subCategories": ("sj_search_tag_subcats", ["sub_category"], [""], True, False),
            "brands": ("sj_search_tag_brands", ["brand"], [""], True, False),
            "collections": ("sj_search_tag_collections", ["collection"], [""], True, False),
            "productIds": ("sj_search_tag_products", ["product_id"], [""], True, False),
            "excludedProductIds": ("sj_search_tag_ex_products", ["product_id"], [""], True, False),
        },
    },
    "sj_delivery_charges": {
        "api_name": "deliveryCharges",
        "child_tables": {
            "tiers": (
                "sj_delivery_charge_tiers",
                ["min_order_value", "max_order_value", "charge"],
                ["min", "max", "charge"],
                False,
                False,
            )
        },
    },
    "sj_delivery_charge_defaults": {
        "api_name": "deliveryChargeDefaults",
        "child_tables": {
            "tiers": (
                "sj_delivery_charge_def_tiers",
                ["min_order_value", "max_order_value", "charge"],
                ["min", "max", "charge"],
                False,
                False,
            )
        },
    },
    "sj_delivery_slots": {
        "api_name": "deliverySlots",
        "child_tables": {
            "slots": (
                "sj_delivery_slot_times",
                ["start_time", "end_time", "capacity"],
                ["startTime", "endTime", "capacity"],
                False,
                False,
            ),
            "pincodes": ("sj_delivery_slot_pincodes", ["pincode"], [""], True, False),
        },
    },
    "sj_delivery_zones": {
        "api_name": "deliveryZones",
        "child_tables": {"pincodes": ("sj_delivery_zone_pincodes", ["pincode"], [""], True, False)},
    },
    "sj_events": {
        "api_name": "events",
        "child_tables": {
            "payload": ("sj_event_payload", ["payload_key", "payload_value"], ["key", "value"], False, True)
        },
    },
}


async def run_db():
    for db_name, config in DB_URLS.items():
        try:
            conn = await aiomysql.connect(**config)
            async with conn.cursor() as cur:
                print(f"[{db_name}] Connected.")
                for parent_table, t_conf in TABLES_CONFIG.items():
                    # Alter table to drop JSON columns
                    drop_cols = list(t_conf["child_tables"].keys())

                    # Convert to snake_case for DB columns if necessary. In schema, they are usually snake_case.
                    def to_snake(name):
                        import re

                        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
                        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

                    snake_cols = [to_snake(c) for c in drop_cols]
                    drop_sql = f"ALTER TABLE {parent_table} " + ", ".join([f"DROP COLUMN {c}" for c in snake_cols])
                    try:
                        await cur.execute(drop_sql)
                    except Exception as e:
                        pass  # Ignore if already dropped

                    # Create child tables
                    for api_key, (child_table, db_cols, api_cols, is_flat, is_kv) in t_conf["child_tables"].items():
                        col_defs = []
                        for c in db_cols:
                            col_defs.append(f"{c} VARCHAR(255)")

                        # If table name is too long, trim it
                        fk_name = f"fk_{child_table[:25]}"

                        create_sql = f"""
                        CREATE TABLE IF NOT EXISTS {child_table} (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            parent_id INT NOT NULL,
                            {", ".join(col_defs)},
                            CONSTRAINT {fk_name} FOREIGN KEY (parent_id) REFERENCES {parent_table}(id) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                        """
                        try:
                            await cur.execute(create_sql)
                        except Exception as e:
                            print(f"[{db_name}] Error creating {child_table}: {e}")

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Migration done.")
        except Exception as e:
            print(f"[{db_name}] Connection error: {e}")


asyncio.run(run_db())
