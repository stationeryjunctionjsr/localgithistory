import re
import os

log_path = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\d87d9ce7-79ea-4843-900e-eacac0995ba9\.system_generated\tasks\task-25246.log"

with open(log_path, 'r', encoding='utf-8') as f:
    log_content = f.read()

# Find all occurrences of "Unknown column 'col_name' in 'clause'"
# Example: Unknown column 'method' in 'where clause'
matches = re.findall(r"Unknown column '([^']+)' in '([^']+)'", log_content)

print(set(matches))
