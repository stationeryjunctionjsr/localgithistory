import re
import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

replace_in_file("backend/app/routers/ads.py", {
    "response_model=Dict[str, Any]": "response_model=MessageResponse"
})

replace_in_file("backend/app/routers/category_tags.py", {
    "@router.get(\"\", response_model=Dict[str, Any])": "@router.get(\"\", response_model=List[CategoryTagResponse])",
    "@router.get(\"/active\", response_model=Dict[str, Any])": "@router.get(\"/active\", response_model=List[CategoryTagResponse])",
    "@router.post(\"\", response_model=Dict[str, Any])": "@router.post(\"\", response_model=CategoryTagResponse)",
    "@router.post(\"/\", response_model=Dict[str, Any])": "@router.post(\"/\", response_model=CategoryTagResponse)",
    "@router.put(\"/{tag_id}\", response_model=Dict[str, Any])": "@router.put(\"/{tag_id}\", response_model=CategoryTagResponse)"
})

print("Done part 1")
