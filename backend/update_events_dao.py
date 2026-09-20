import re

with open('app/db/mysql_events_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the payload looping logic with flat column inserts
replacement = '''
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        
        if getattr(data, "eventType", None) is not None:
            cols.append("event_type")
            vals.append(":eventType")
            params["eventType"] = data.eventType
            
        # Map flat payload items if payload exists
        if data.payload is not None:
            for item in data.payload:
                # We map keys to columns safely
                col_name = item.key
                if col_name == "ipAddress": col_name = "ip_address"
                elif col_name == "testRunId": col_name = "test_run_id"
                elif col_name == "productId": col_name = "product_id"
                elif col_name == "productName": col_name = "product_name"
                elif col_name == "sessionId": col_name = "session_id"
                elif col_name == "userId": col_name = "user_id"
                elif col_name == "resultsCount": col_name = "results_count"
                
                # Device fields are handled separately or directly
                # If a device object was passed and exploded in the router, it will have exact column names
                
                # Ensure column is alphanumeric to prevent SQL injection
                if re.match(r'^[a-zA-Z0-9_]+$', col_name):
                    cols.append(col_name)
                    vals.append(f":{col_name}")
                    params[col_name] = item.value
                    
        # Explicitly map tracking_id if it exists
        if getattr(data, "tracking_id", None) is not None:
            cols.append("tracking_id")
            vals.append(":tracking_id")
            params["tracking_id"] = data.tracking_id
            
        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
'''

text = re.sub(r'        cols = \["external_id", "created_at", "updated_at"\].*?            if data\.payload is not None:.*?                for item in data\.payload:.*?                    await session\.execute.*?                        text\("INSERT INTO sj_event_payload.*?                        \{"pid": new_id, "k": item\.key, "v": item\.value\}.*?                    \).*?            await session\.commit\(\)', replacement, text, flags=re.DOTALL)

with open('app/db/mysql_events_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated events DAO to use flat columns")
