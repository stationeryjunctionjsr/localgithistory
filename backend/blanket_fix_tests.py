import os
import re

tests_dir = 'tests'

replacements = [
    (r'\.isApplicableToRole', '.is_applicable_to_role'),
    (r'\.zoneId', '.zone_id'),
    (r'\.zoneDefaultCapacity', '.zone_default_capacity'),
    (r'\.startTime', '.start_time'),
    (r'\.endTime', '.end_time'),
    (r'\.isActive', '.is_active'),
    (r'\.isUrgent', '.is_urgent'),
    (r'\.bookedCount', '.booked_count'),
    (r'\.cutoffHours', '.cutoff_hours'),
    (r'\.urgentCutoffHours', '.urgent_cutoff_hours'),
    # Fix dict-like get on Pydantic models (common in loops over DB results)
    (r'\.get\("isActive"\)', '.is_active'),
    (r'\.get\("method"\)', '.method'),
    (r'\.get\("typeOfDiscount"\)', '.type_of_discount'),
    (r'\.get\("appliesToValueIds"\)', '.applies_to_value_ids'),
]

for root, _, files in os.walk(tests_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
