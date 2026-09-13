import re

with open('frontend/src/components/MobileNavBar.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'(?s)const ProfileIcon: React\.FC = \(\) => \(\s*<svg.*?</svg>\s*\);\s*'
replacement = r''

new_content = re.sub(pattern, replacement, content)

with open('frontend/src/components/MobileNavBar.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
