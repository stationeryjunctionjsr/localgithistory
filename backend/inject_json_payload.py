filename = 'app/models/base.py'
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

import_statement = "import typing\n\nJsonPayload = typing.Dict[str, typing.Any]\n\n"
content = import_statement + content

with open(filename, 'w', encoding='utf-8') as f:
    f.write(content)
