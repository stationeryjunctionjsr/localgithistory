with open('app/db/mysql_supportTickets_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# UPDATE SELECT
old_select = '''        q_responses = text(f"SELECT parent_id, admin_id, message FROM sj_ticket_responses WHERE parent_id IN ({id_list})")
        res_responses = await session.execute(q_responses)
        rows_responses = res_responses.fetchall()

        for r in rows_responses:
            if "responses" not in c_map[r.parent_id]:
                c_map[r.parent_id]["responses"] = []
            
            c_map[r.parent_id]["responses"].append(
                {"user": r[1], "message": r[2]}
            )'''

new_select = '''        q_responses = text(f"SELECT parent_id, admin_id, message, is_admin_response, attachments FROM sj_ticket_responses WHERE parent_id IN ({id_list})")
        res_responses = await session.execute(q_responses)
        rows_responses = res_responses.fetchall()

        import json

        for r in rows_responses:
            if "responses" not in c_map[r.parent_id]:
                c_map[r.parent_id]["responses"] = []
            
            try:
                atts = json.loads(r[4]) if r[4] else []
            except Exception:
                atts = []

            c_map[r.parent_id]["responses"].append(
                {"user": r[1], "message": r[2], "isAdminResponse": bool(r[3]), "attachments": atts}
            )'''
text = text.replace(old_select, new_select)

# UPDATE DELETE/INSERT
old_insert = '''        if getattr(data, "responses", None) is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"SELECT id FROM sj_ticket_responses WHERE parent_id = :id LIMIT 1"),
                {"id": pk}
            )
            if result.rowcount > 0:
                 return  # cannot safely replace children without primary key handling

            child_list = data.responses or []

            if child_list:
                for item in child_list:
                    p = {"id": pk}

                    p["v0"] = item.user
                    p["v1"] = item.message
                    await session.execute(text(f"INSERT INTO sj_ticket_responses (parent_id, admin_id, message) VALUES (:id, :v0, :v1)"), p)'''

new_insert = '''        if getattr(data, "responses", None) is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"SELECT id FROM sj_ticket_responses WHERE parent_id = :id LIMIT 1"),
                {"id": pk}
            )
            if result.rowcount > 0:
                 return  # cannot safely replace children without primary key handling

            child_list = data.responses or []

            import json
            if child_list:
                for item in child_list:
                    p = {"id": pk}

                    p["v0"] = item.user
                    p["v1"] = item.message
                    p["v2"] = item.isAdminResponse
                    p["v3"] = json.dumps(item.attachments) if item.attachments else None
                    await session.execute(text(f"INSERT INTO sj_ticket_responses (parent_id, admin_id, message, is_admin_response, attachments) VALUES (:id, :v0, :v1, :v2, :v3)"), p)'''
text = text.replace(old_insert, new_insert)

old_update = '''        if getattr(data, "responses", None) is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": row_id})
            child_list = data.responses or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.user
                    p["v1"] = item.message
                    await session.execute(text(f"INSERT INTO sj_ticket_responses (parent_id, admin_id, message) VALUES (:id, :v0, :v1)"), p)'''

new_update = '''        if getattr(data, "responses", None) is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": row_id})
            child_list = data.responses or []

            import json
            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.user
                    p["v1"] = item.message
                    p["v2"] = item.isAdminResponse
                    p["v3"] = json.dumps(item.attachments) if item.attachments else None
                    await session.execute(text(f"INSERT INTO sj_ticket_responses (parent_id, admin_id, message, is_admin_response, attachments) VALUES (:id, :v0, :v1, :v2, :v3)"), p)'''
text = text.replace(old_update, new_update)

with open('app/db/mysql_supportTickets_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
