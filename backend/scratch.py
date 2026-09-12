import os, re
candidates = [f for f in os.listdir('app/db') if f.endswith('_dao.py') and not f.startswith('mysql_') and f != 'typed_doc_dao.py']

usages = {}
for root, dirs, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root: continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for cand in candidates:
                        mod = cand[:-3]
                        # check for whole word
                        if re.search(r'\b' + re.escape(mod) + r'\b', content):
                            usages.setdefault(cand, []).append(path)
            except: pass

for cand in candidates:
    if cand in usages:
        print(f'{cand} is used in {usages[cand]}')
    else:
        print(f'{cand} is UNUSED')

