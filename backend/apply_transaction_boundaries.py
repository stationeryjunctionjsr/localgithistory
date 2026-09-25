import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_async_with = False
async_with_indent = 0
buffer = []

for line in lines:
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    if stripped == 'async with factory() as session:':
        new_lines.append(line)
        new_lines.append(' ' * (indent + 4) + 'try:\n')
        in_async_with = True
        async_with_indent = indent
        continue
        
    if in_async_with:
        # Check if we exited the async with block
        if stripped != '' and indent <= async_with_indent:
            in_async_with = False
            # We exited, so we need to add the except block BEFORE this line
            new_lines.append(' ' * (async_with_indent + 4) + 'except Exception as e:\n')
            new_lines.append(' ' * (async_with_indent + 8) + 'await session.rollback()\n')
            new_lines.append(' ' * (async_with_indent + 8) + 'raise e\n')
            new_lines.append(line)
        else:
            if line.strip() == '':
                new_lines.append(line)
            else:
                new_lines.append(' ' * 4 + line) # Add 4 spaces of indentation
    else:
        new_lines.append(line)

# Handle case where file ends inside async with
if in_async_with:
    new_lines.append(' ' * (async_with_indent + 4) + 'except Exception as e:\n')
    new_lines.append(' ' * (async_with_indent + 8) + 'await session.rollback()\n')
    new_lines.append(' ' * (async_with_indent + 8) + 'raise e\n')

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("SUCCESS")
