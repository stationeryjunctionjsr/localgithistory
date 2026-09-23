import json
import os

target_files = [
    "full_pytest_run_ok.txt",
    "pytest_functional_run.txt",
    "pytest_with_timeout.txt",
    "referral_frontend_matches.json"
]

brain_dir = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain"

for root, _, files in os.walk(brain_dir):
    for filename in files:
        if filename == "transcript_full.jsonl":
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not any(tf in line for tf in target_files): continue
                        data = json.loads(line)
                        if "tool_calls" in data:
                            for tc in data["tool_calls"]:
                                if tc["name"] in ["default_api:run_command", "run_command"]:
                                    cmd = tc.get("args", {}).get("CommandLine", "")
                                    for tf in target_files:
                                        if f">{tf}" in cmd.replace(" ", "") or f"> {tf}" in cmd:
                                            # Found creation command
                                            print(f"FOUND creation of {tf}: {cmd[:200]}")
                        
                        if "content" in data:
                            content = data["content"]
                            if "Output:\n" in content:
                                for tf in target_files:
                                    if tf in content:
                                        print(f"FOUND {tf} in output!")
            except Exception as e:
                pass
