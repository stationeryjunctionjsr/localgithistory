import json

with open('transcript_edits.jsonl', 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: data = json.loads(line)
        except: continue
        if 'tool_calls' not in data: continue
        for call in data['tool_calls']:
            args = call.get('args', {})
            tfile = args.get('TargetFile', '')
            if 'returns.py' in tfile:
                target = args.get('TargetContent', '')
                if isinstance(target, str) and target.startswith('"'):
                    target = json.loads(target)
                print("TARGET:\n" + target)
                rep = args.get('ReplacementContent', '')
                if isinstance(rep, str) and rep.startswith('"'):
                    rep = json.loads(rep)
                print("REPLACEMENT:\n" + rep)
                print("-" * 80)
