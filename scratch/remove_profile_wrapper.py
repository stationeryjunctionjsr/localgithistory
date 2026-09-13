import re

with open('frontend/src/components/MobileNavBar.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'(?s) *<div className=\{styles\.profileWrapper\} ref=\{profileDropdownRef\}>.*?</button>\s*</>\s*\)\s*:\s*\(\s*<>\s*<button.*?</button>\s*</>\s*\)\}\s*</div>\s*\)\}\s*</div>\s*<button className=\{styles\.menuToggle\}'
replacement = r'            <button className={styles.menuToggle}'

new_content = re.sub(pattern, replacement, content)

with open('frontend/src/components/MobileNavBar.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
