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
                        if "referral_frontend_matches" in line or "full_pytest_run_ok" in line:
                            data = json.loads(line)
                            if data.get("source") == "MODEL" and data.get("type") == "PLANNER_RESPONSE":
                                if "content" in data:
                                    print(f"--- MODEL THOUGHT/CONTENT ---")
                                    print(data["content"][:1000])
                                if "thinking" in data:
                                    print(f"--- MODEL THINKING ---")
                                    print(data["thinking"][:1000])
            except Exception as e:
                pass
