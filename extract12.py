import json
import os

brain_dir = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain"

for root, _, files in os.walk(brain_dir):
    for filename in files:
        if filename == "transcript_full.jsonl":
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "full_pytest_run_ok" in line:
                            data = json.loads(line)
                            if "tool_calls" in data:
                                for tc in data["tool_calls"]:
                                    if tc["name"] in ["default_api:run_command", "run_command"]:
                                        cmd = tc.get("args", {}).get("CommandLine", "")
                                        if "full_pytest_run_ok" in cmd:
                                            print(f"FOUND cmd: {cmd[:200]}")
            except Exception as e:
                pass
