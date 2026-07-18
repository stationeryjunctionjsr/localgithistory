import json, os, glob

paths = glob.glob(r'C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\*\.system_generated\logs\transcript.jsonl')
res = []

for p in paths:
    if not os.path.exists(p): continue
    with open(p, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
                for tc in d.get('tool_calls', []):
                    if tc.get('name') in ('replace_file_content', 'multi_replace_file_content'):
                        args = tc.get('arguments', {})
                        fpath = args.get('TargetFile', '')
                        if 'AuthContext.tsx' in fpath or 'api-client' in fpath:
                            res.append({'file': fpath, 'args': args})
            except Exception:
                pass

with open('history_output.json', 'w', encoding='utf-8') as out:
    json.dump(res, out, indent=2)

print(f"Found {len(res)} file modifications. Output written to history_output.json")
