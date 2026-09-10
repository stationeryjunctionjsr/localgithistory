import sys

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old not in content:
            print(f"ERROR: Target string not found!\n\nTarget:\n{old}")
            sys.exit(1)
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replacements successful.")

replacements = [
    # Add to all 4 query strings (2x SELECT, 1x INSERT cols, 1x INSERT params)
    (
        'valet_decline_history,\n                           shipped_at',
        'valet_decline_history, is_urgent_delivery,\n                           shipped_at'
    ),
    (
        'valet_decline_history,\n                             shipped_at',
        'valet_decline_history, is_urgent_delivery,\n                             shipped_at'
    ),
    (
        'valet_decline_history,\n                          shipped_at',
        'valet_decline_history, is_urgent_delivery,\n                          shipped_at'
    ),
    (
        'valet_decline_history,\n                                                  :shipped_at',
        'valet_decline_history, :is_urgent_delivery,\n                                                  :shipped_at'
    ),
    (
        '_row_to_doc',
        '_row_to_doc'
    )
]

try:
    replace_in_file("backend/app/db/mysql_order_dao.py", replacements)
except Exception as e:
    print(e)
