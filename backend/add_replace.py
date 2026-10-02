filepath = 'app/db/mysql_banner_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

func = """
    async def _replace_children(self, session, bid: int, data):
        from sqlalchemy import text
        await session.execute(text("DELETE FROM sj_banner_user_segments WHERE banner_id = :bid"), {"bid": bid})
        await session.execute(text("DELETE FROM sj_banner_visibility_rules WHERE banner_id = :bid"), {"bid": bid})
        
        user_segments = getattr(data, 'user_segments', [])
        for seg in (user_segments if user_segments is not None else []):
            await session.execute(
                text("INSERT INTO sj_banner_user_segments (banner_id, segment) VALUES (:bid, :seg)"),
                {"bid": bid, "seg": seg}
            )
            
        visibility_rules = getattr(data, 'visibility_rules', [])
        for rule in (visibility_rules if visibility_rules is not None else []):
            rule_val = rule.model_dump_json() if hasattr(rule, 'model_dump_json') else str(rule)
            await session.execute(
                text("INSERT INTO sj_banner_visibility_rules (banner_id, rule) VALUES (:bid, :rule)"),
                {"bid": bid, "rule": rule_val}
            )
"""

content += "\n" + func

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
