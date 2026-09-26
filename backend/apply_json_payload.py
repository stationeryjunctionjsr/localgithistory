import os

replacements = {
    "app/utils/email_otp.py": [
        ("-> Tuple[bool, dict]:", "-> Tuple[bool, 'JsonPayload']:"),
        ("-> dict:", "-> 'JsonPayload':"),
        ("-> Optional[dict]:", "-> Optional['JsonPayload']:"),
        ("user_record: dict", "user_record: 'JsonPayload'"),
        ("Dict[str, dict]", "Dict[str, 'JsonPayload']")
    ],
    "app/utils/otp.py": [
        ("-> Tuple[bool, dict]:", "-> Tuple[bool, 'JsonPayload']:"),
        ("-> dict:", "-> 'JsonPayload':"),
        ("-> Optional[dict]:", "-> Optional['JsonPayload']:"),
        ("user_record: dict", "user_record: 'JsonPayload'"),
        ("Dict[str, dict]", "Dict[str, 'JsonPayload']"),
        ("payload: dict", "payload: 'JsonPayload'"),
        ("value: dict", "value: 'JsonPayload'")
    ]
}

for filepath, reps in replacements.items():
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "from app.models.base import JsonPayload" not in content:
            content = "from app.models.base import JsonPayload\n" + content
            
        for old, new in reps:
            content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
