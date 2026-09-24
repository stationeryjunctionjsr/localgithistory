import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the post-filtering logic from findAll
post_filter = '''        if query:
            filtered = []
            for doc in docs:
                match = True
                for k, v in query.items():
                    if k in ('allowed_ids',):
                        continue
                    if k in ('_id', 'id'):
                        if doc.id != str(v) and doc.id != v:
                            match = False
                            break
                    elif (doc[k] if k in doc else None) != v:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            return filtered'''

text = text.replace(post_filter, '        pass')

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
