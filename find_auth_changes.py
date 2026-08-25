import glob
import json

paths = glob.glob(r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\*\.system_generated\logs\transcript.jsonl")
paths.sort(key=lambda x: x)  # You can sort by mtime if needed

for p in paths:
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for tc in d.get("tool_calls", []):
                    args = tc.get("arguments", {})
                    fpath = args.get("TargetFile", "")
                    if "AuthContext.tsx" in fpath:
                        print(f"FOUND IN {p}")
                        print("Tool:", tc.get("name"))
                        print("StartLine:", args.get("StartLine"))
                        print("EndLine:", args.get("EndLine"))
                        print("TargetContent:", repr(args.get("TargetContent", "")))
                        print("ReplacementContent:", repr(args.get("ReplacementContent", "")))
                        print("=" * 80)
    except Exception as e:
        pass
