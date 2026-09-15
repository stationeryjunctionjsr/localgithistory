"""
Auto-generated DAOs for tables that were refactored from JSON clobs to relational child tables.
"""

import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.flat_relational_configs import FLAT_RELATIONAL_DAOS
from app.db.db_utils import now_utc


class DynamicRelationalDAO:
    def __init__(self, table_name: str, config: Dict):
        self.table_name = table_name
        self.config = config
        # Fetch the original scalar_map from the old config
        api_name = config["api_name"]
        self.flat_relational_dao = FLAT_RELATIONAL_DAOS[api_name] if api_name in FLAT_RELATIONAL_DAOS else None
        self.scalar_map = self.flat_relational_dao.scalar_map if self.flat_relational_dao else {}
        self.bool_keys = self.flat_relational_dao.bool_api_keys if self.flat_relational_dao else set()

    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"{self.table_name}{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, r, children: Dict) -> Any:
        # Strictly enforce direct access without .get or hasattr fallbacks where possible
        rm = r._mapping
        
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()
            
        rev = {v: k for k, v in self.scalar_map.items()}
        for db_col, api_key in rev.items():
            val = rm[db_col]
            if api_key in self.bool_keys:
                val = bool(val)
            out[api_key] = val
        for k, v in children.items():
            out[k] = v
        schema_cls = self.flat_relational_dao.schema_cls if self.flat_relational_dao else None
        return schema_cls(**out) if schema_cls else out

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        for rid in ids:
            for api_key, c_conf in self.config["child_tables"].items():
                is_flat = c_conf[3]
                is_kv = c_conf[4]
                if is_kv:
                    c_map[rid][api_key] = {}
                else:
                    c_map[rid][api_key] = []
        if not ids:
            return c_map

        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            for api_key, c_conf in self.config["child_tables"].items():
                child_table = c_conf[0]
                db_cols = c_conf[1]
                api_cols = c_conf[2]
                is_flat = c_conf[3]
                is_kv = c_conf[4]
                sql = text(
                    f"SELECT parent_id, {', '.join(db_cols)} FROM {child_table} WHERE parent_id IN ({placeholders})"
                )
                res = await session.execute(sql, chunk_params)
                for row in res.fetchall():
                    if is_flat:
                        c_map[row.parent_id][api_key].append(row._mapping[db_cols[0]])
                    elif is_kv:
                        k = row._mapping[db_cols[0]]
                        v = row._mapping[db_cols[1]]
                        c_map[row.parent_id][api_key][k] = v
                    else:
                        obj = {}
                        for i, db_c in enumerate(db_cols):
                            obj[api_cols[i]] = row._mapping[db_c]
                        c_map[row.parent_id][api_key].append(obj)
        return c_map

    async def _replace_children(self, session, p_id: int, data: Any):
        for api_key, c_conf in self.config["child_tables"].items():
            child_table = c_conf[0]
            db_cols = c_conf[1]
            api_cols = c_conf[2]
            is_flat = c_conf[3]
            is_kv = c_conf[4]
            await session.execute(text(f"DELETE FROM {child_table} WHERE parent_id = :pid"), {"pid": p_id})
            
            if isinstance(data, dict):
                val = data[api_key] if api_key in data else None
            else:
                val = data.__dict__[api_key] if api_key in data.__dict__ else None
            if not val:
                continue
            if is_flat:
                for item in val:
                    sql = text(f"INSERT INTO {child_table} (parent_id, {db_cols[0]}) VALUES (:pid, :val)")
                    await session.execute(sql, {"pid": p_id, "val": str(item)})
            elif is_kv:
                for k, v in val.items():
                    sql = text(
                        f"INSERT INTO {child_table} (parent_id, {db_cols[0]}, {db_cols[1]}) VALUES (:pid, :k, :v)"
                    )
                    await session.execute(sql, {"pid": p_id, "k": str(k), "v": str(v)})
            else:
                for item in val:
                    cols_sql = ", ".join(db_cols)
                    vals_sql = ", ".join([f":v{i}" for i in range(len(db_cols))])
                    sql = text(f"INSERT INTO {child_table} (parent_id, {cols_sql}) VALUES (:pid, {vals_sql})")
                    params = {"pid": p_id}
                    for i, a_col in enumerate(api_cols):
                        if isinstance(item, dict):
                            val_i = item[a_col] if a_col in item and item[a_col] is not None else ""
                        else:
                            val_i = item.__dict__[a_col] if a_col in item.__dict__ and item.__dict__[a_col] is not None else ""
                        params[f"v{i}"] = str(val_i)
                    await session.execute(sql, params)

    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k in self.scalar_map:
                    where_clauses.append(f"{self.scalar_map[k]} = :{k}")
                    params[k] = v
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            res = await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params)
            rows = res.fetchall()
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [self.__map_to_schema(r, c_map[r.id]) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Any]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def create(self, data: Any) -> Any:
        data_dict = data if isinstance(data, dict) else data.__dict__
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}
        for api_k, db_col in self.scalar_map.items():
            if api_k in data_dict:
                cols.append(db_col)
                params[f"s_{api_k}"] = data_dict[api_k]
        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k, db in self.scalar_map.items() if k in data_dict])
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        existing_dict = existing if isinstance(existing, dict) else existing.__dict__
        data_dict = data if isinstance(data, dict) else data.__dict__
        merged = {**existing_dict, **data_dict}
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": int(id) if str(id).isdigit() else None, "u": now}
        for api_k, db_col in self.scalar_map.items():
            if api_k in merged:
                updates.append(f"{db_col} = :s_{api_k}")
                params[f"s_{api_k}"] = merged[api_k]
        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"), params)
            await self._replace_children(session, int(id) if str(id).isdigit() else None, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return res.rowcount > 0


TABLES_CONFIG = {
    "sj_coupons": {
        "api_name": "coupons",
        "child_tables": {
            "quantityTiers": ("sj_coupon_quantity_tiers", ["min_qty", "discount_value"], ["minQuantity", "discountValue"], False, False),
            "applicableRoles": ("sj_coupon_roles", ["role"], [""], True, False),
            "applicableUserIds": ("sj_coupon_users", ["user_id"], [""], True, False),
            "applicableCategories": ("sj_coupon_categories", ["category"], [""], True, False),
            "appliesToValueIds": ("sj_coupon_applies_to_values", ["value_id"], [""], True, False),
            "excludedProductIds": ("sj_coupon_excluded_products", ["product_id"], [""], True, False)
        }
    },

    "sj_activities": {
        "api_name": "activities",
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
GENERATED_DAOS = {}
for t, conf in TABLES_CONFIG.items():
    GENERATED_DAOS[conf["api_name"]] = DynamicRelationalDAO(t, conf)




