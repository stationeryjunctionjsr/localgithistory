import json
import os

target_files = [
    "PERSISTENCE_AUDIT_2026-09-17.md",
    "pydantic_app_only_scan_report.md",
    "pydantic_scan_report.md",
    "script.py"
]

brain_dir = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain"

for root, _, files in os.walk(brain_dir):
    for filename in files:
        if filename.endswith(".jsonl"):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        for tf in target_files:
                            if tf in line:
                                print(f"Found {tf} in {filepath}")
            except Exception as e:
                pass
