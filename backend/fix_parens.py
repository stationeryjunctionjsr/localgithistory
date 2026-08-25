import glob
import re

files = glob.glob("c:/Ecommerce app/backend/app/routers/*.py")

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content

    # Let's fix any line that starts with @router. and is missing a closing parenthesis.
    # It looks like: @router.post("", status_code=201\n or @router.post("", status_code=201\r\n

    def fix_missing_paren(match):
        line = match.group(0)
        # if the line does not end with ) before the newline or \r
        stripped = line.rstrip("\r\n")
        if not stripped.endswith(")"):
            return stripped + ")\n"
        return line

    new_content = re.sub(r"^@router\.[a-z]+\(\"\"[^\n]+", fix_missing_paren, new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^@router\.[a-z]+\(\'\'[^\n]+", fix_missing_paren, new_content, flags=re.MULTILINE)

    if new_content != content:
        print(f"Fixed parenthesis in {file}")
        with open(file, "w", encoding="utf-8") as f:
            f.write(new_content)
