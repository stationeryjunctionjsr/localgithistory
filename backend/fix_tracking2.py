import re
import json

with open("app/db/mysql_tracking_dao.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """            elif api_k in ("cartValue",) and val is not None:
                val = float(val)
            elif api_k in ("isReturning",) and val is not None:
                val = bool(val)
            elif api_k in ("cartItems",) and val is not None:
                if isinstance(val, str):
                    import json
                    try: val = json.loads(val)
                    except: pass"""

content = content.replace(
    """            elif api_k in ("cartValue",) and val is not None:
                val = float(val)""",
    replacement,
)

# We also need to serialize cartItems when inserting/updating!
serialize_replacement = """                val = data[api_k]
                if api_k == "timestamp" and val:
                    try: val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except: pass
                if api_k == "cartItems" and val is not None:
                    import json
                    val = json.dumps(val)
                params[f"s_{api_k}"] = val"""

content = content.replace(
    """                val = data[api_k]
                if api_k == "timestamp" and val:
                    try: val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except: pass
                params[f"s_{api_k}"] = val""",
    serialize_replacement,
)

serialize_merged_replacement = """                val = merged[api_k]
                if api_k == "timestamp" and val:
                    try: val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except: pass
                if api_k == "cartItems" and val is not None:
                    import json
                    val = json.dumps(val)
                params[f"s_{api_k}"] = val"""

content = content.replace(
    """                val = merged[api_k]
                if api_k == "timestamp" and val:
                    try: val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except: pass
                params[f"s_{api_k}"] = val""",
    serialize_merged_replacement,
)

with open("app/db/mysql_tracking_dao.py", "w", encoding="utf-8") as f:
    f.write(content)
