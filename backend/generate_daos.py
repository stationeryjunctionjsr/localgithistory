# Copy config here
TABLES_CONFIG = {
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

OUT_FILE = "backend/app/db/mysql_generated_daos.py"


def generate():
    code = [
        '"""',
        "Auto-generated DAOs for tables that were refactored from JSON clobs to relational child tables.",
        '"""',
        "import secrets",
        "from datetime import datetime",
        "from typing import Dict, List, Optional",
        "from sqlalchemy import text",
        "from app.config.database import get_async_session_factory",
        "from app.config.settings import settings",
        "from app.db.oracle_utils import now_utc",
        "from app.db.mysql_typed_doc_configs import TYPED_DOC_DAOS",
        "",
    ]

    # We will build a unified class that uses TYPED_DOC_DAOS for the base scalar_map
    # but handles the child tables explicitly via the config.
    code.append("class DynamicRelationalDAO:")
    code.append("    def __init__(self, table_name: str, config: Dict):")
    code.append("        self.table_name = table_name")
    code.append("        self.config = config")
    code.append("        # Fetch the original scalar_map from the old typed_doc config")
    code.append('        api_name = config["api_name"]')
    code.append("        self.typed_doc_dao = TYPED_DOC_DAOS.get(api_name)")
    code.append("        self.scalar_map = self.typed_doc_dao.scalar_map if self.typed_doc_dao else {}")
    code.append("        self.bool_keys = self.typed_doc_dao.bool_api_keys if self.typed_doc_dao else set()")
    code.append("")
    code.append("    @property")
    code.append("    def TABLE(self):")
    code.append('        suffix = getattr(settings, "table_suffix", "")')
    code.append('        return f"{self.table_name}{suffix}"')
    code.append("")
    code.append("    def _factory(self):")
    code.append("        return get_async_session_factory()")
    code.append("")
    code.append("    def _row_to_dict(self, r, children: Dict) -> Dict:")
    code.append('        out = {"_id": str(r.id), "externalId": getattr(r, "external_id", None)}')
    code.append('        if hasattr(r, "created_at") and r.created_at: out["createdAt"] = r.created_at.isoformat()')
    code.append('        if hasattr(r, "updated_at") and r.updated_at: out["updatedAt"] = r.updated_at.isoformat()')
    code.append("        rev = {v: k for k, v in self.scalar_map.items()}")
    code.append("        for db_col, api_key in rev.items():")
    code.append("            val = getattr(r, db_col, None)")
    code.append("            if api_key in self.bool_keys: val = bool(val)")
    code.append("            out[api_key] = val")
    code.append("        for k, v in children.items():")
    code.append("            out[k] = v")
    code.append("        return out")
    code.append("")
    code.append("    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:")
    code.append("        c_map = {rid: {} for rid in ids}")
    code.append("        for rid in ids:")
    code.append('            for api_key, c_conf in self.config["child_tables"].items():')
    code.append("                is_flat = c_conf[3]")
    code.append("                is_kv = c_conf[4]")
    code.append("                if is_kv:")
    code.append("                    c_map[rid][api_key] = {}")
    code.append("                else:")
    code.append("                    c_map[rid][api_key] = []")
    code.append("        if not ids: return c_map")
    code.append("        ")
    code.append("        chunks = [ids[i:i+999] for i in range(0, len(ids), 999)]")
    code.append("        for chunk in chunks:")
    code.append('            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}')
    code.append('            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])')
    code.append('            for api_key, c_conf in self.config["child_tables"].items():')
    code.append("                child_table = c_conf[0]")
    code.append("                db_cols = c_conf[1]")
    code.append("                api_cols = c_conf[2]")
    code.append("                is_flat = c_conf[3]")
    code.append("                is_kv = c_conf[4]")
    code.append(
        '                sql = text(f"SELECT parent_id, {\\", \\".join(db_cols)} FROM {child_table} WHERE parent_id IN ({placeholders})")'
    )
    code.append("                res = await session.execute(sql, chunk_params)")
    code.append("                for row in res.fetchall():")
    code.append("                    if is_flat:")
    code.append("                        c_map[row.parent_id][api_key].append(getattr(row, db_cols[0]))")
    code.append("                    elif is_kv:")
    code.append("                        k = getattr(row, db_cols[0])")
    code.append("                        v = getattr(row, db_cols[1])")
    code.append("                        c_map[row.parent_id][api_key][k] = v")
    code.append("                    else:")
    code.append("                        obj = {}")
    code.append("                        for i, db_c in enumerate(db_cols):")
    code.append("                            obj[api_cols[i]] = getattr(row, db_c)")
    code.append("                        c_map[row.parent_id][api_key].append(obj)")
    code.append("        return c_map")
    code.append("")
    code.append("    async def _replace_children(self, session, p_id: int, data: Dict):")
    code.append('        for api_key, c_conf in self.config["child_tables"].items():')
    code.append("            child_table = c_conf[0]")
    code.append("            db_cols = c_conf[1]")
    code.append("            api_cols = c_conf[2]")
    code.append("            is_flat = c_conf[3]")
    code.append("            is_kv = c_conf[4]")
    code.append(
        '            await session.execute(text(f"DELETE FROM {child_table} WHERE parent_id = :pid"), {"pid": p_id})'
    )
    code.append("            val = data.get(api_key)")
    code.append("            if not val: continue")
    code.append("            if is_flat:")
    code.append("                for item in val:")
    code.append(
        '                    sql = text(f"INSERT INTO {child_table} (parent_id, {db_cols[0]}) VALUES (:pid, :val)")'
    )
    code.append('                    await session.execute(sql, {"pid": p_id, "val": str(item)})')
    code.append("            elif is_kv:")
    code.append("                for k, v in val.items():")
    code.append(
        '                    sql = text(f"INSERT INTO {child_table} (parent_id, {db_cols[0]}, {db_cols[1]}) VALUES (:pid, :k, :v)")'
    )
    code.append('                    await session.execute(sql, {"pid": p_id, "k": str(k), "v": str(v)})')
    code.append("            else:")
    code.append("                for item in val:")
    code.append('                    cols_sql = ", ".join(db_cols)')
    code.append('                    vals_sql = ", ".join([f":v{i}" for i in range(len(db_cols))])')
    code.append(
        '                    sql = text(f"INSERT INTO {child_table} (parent_id, {cols_sql}) VALUES (:pid, {vals_sql})")'
    )
    code.append('                    params = {"pid": p_id}')
    code.append("                    for i, a_col in enumerate(api_cols):")
    code.append('                        params[f"v{i}"] = str(item.get(a_col, ""))')
    code.append("                    await session.execute(sql, params)")
    code.append("")
    code.append("    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:")
    code.append("        factory = self._factory()")
    code.append("        if not factory: return []")
    code.append("        where_clauses = []")
    code.append("        params = {}")
    code.append("        if query:")
    code.append("            for k, v in query.items():")
    code.append('                if k in ("_id", "id"):')
    code.append('                    where_clauses.append("id = :id")')
    code.append('                    params["id"] = int(v) if str(v).isdigit() else 0')
    code.append("                elif k in self.scalar_map:")
    code.append('                    where_clauses.append(f"{self.scalar_map[k]} = :{k}")')
    code.append("                    params[k] = v")
    code.append('        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"')
    code.append("        async with factory() as session:")
    code.append(
        '            res = await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params)'
    )
    code.append("            rows = res.fetchall()")
    code.append("            c_map = await self._fetch_children(session, [r.id for r in rows])")
    code.append("        return [self._row_to_dict(r, c_map[r.id]) for r in rows]")
    code.append("")
    code.append("    async def findOne(self, query: Dict) -> Optional[Dict]:")
    code.append("        docs = await self.findAll(query)")
    code.append("        return docs[0] if docs else None")
    code.append("")
    code.append("    async def findById(self, id: str) -> Optional[Dict]:")
    code.append('        return await self.findOne({"_id": id})')
    code.append("")
    code.append("    async def create(self, data: Dict) -> Dict:")
    code.append("        factory = self._factory()")
    code.append("        now = now_utc()")
    code.append("        external_id = secrets.token_hex(16)")
    code.append('        cols = ["external_id", "created_at", "updated_at"]')
    code.append('        params = {"eid": external_id, "c": now, "u": now}')
    code.append("        for api_k, db_col in self.scalar_map.items():")
    code.append("            if api_k in data:")
    code.append("                cols.append(db_col)")
    code.append('                params[f"s_{api_k}"] = data[api_k]')
    code.append('        col_sql = ", ".join(cols)')
    code.append(
        '        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k, db in self.scalar_map.items() if k in data])'
    )
    code.append("        async with factory() as session:")
    code.append(
        '            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)'
    )
    code.append(
        '            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id})).scalar()'
    )
    code.append("            await self._replace_children(session, new_id, data)")
    code.append("            await session.commit()")
    code.append("        return await self.findById(str(new_id))")
    code.append("")
    code.append("    async def update(self, id: str, data: Dict) -> Optional[Dict]:")
    code.append("        existing = await self.findById(id)")
    code.append("        if not existing: return None")
    code.append("        merged = {**existing, **data}")
    code.append("        now = now_utc()")
    code.append('        updates = ["updated_at = :u"]')
    code.append('        params = {"id": int(id) if str(id).isdigit() else 0, "u": now}')
    code.append("        for api_k, db_col in self.scalar_map.items():")
    code.append("            if api_k in merged:")
    code.append('                updates.append(f"{db_col} = :s_{api_k}")')
    code.append('                params[f"s_{api_k}"] = merged[api_k]')
    code.append('        set_sql = ", ".join(updates)')
    code.append("        factory = self._factory()")
    code.append("        async with factory() as session:")
    code.append('            await session.execute(text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"), params)')
    code.append("            await self._replace_children(session, int(id) if str(id).isdigit() else 0, merged)")
    code.append("            await session.commit()")
    code.append("        return await self.findById(id)")
    code.append("")
    code.append("    async def delete(self, id: str) -> bool:")
    code.append("        factory = self._factory()")
    code.append("        async with factory() as session:")
    code.append(
        '            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else 0})'
    )
    code.append("            await session.commit()")
    code.append("            return res.rowcount > 0")
    code.append("")

    code.append(f"TABLES_CONFIG = {repr(TABLES_CONFIG)}")
    code.append("GENERATED_DAOS = {}")
    code.append("for t, conf in TABLES_CONFIG.items():")
    code.append("    GENERATED_DAOS[conf['api_name']] = DynamicRelationalDAO(t, conf)")
    code.append("")

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(code))


generate()
