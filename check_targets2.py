import json

def unescape(s):
    if isinstance(s, str) and s.startswith('"'):
        s = s[1:-1]
        s = s.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t').replace('\\\\', '\\')
    return s.replace('\r\n', '\n')

count = 0
for line in open('transcript_edits.jsonl', 'r', encoding='utf-8-sig'):
    if not line.strip(): continue
    try: data = json.loads(line)
    except: continue
    if 'tool_calls' not in data: continue
    for call in data['tool_calls']:
        args = call.get('args', {})
        tfile = unescape(args.get('TargetFile', ''))
        if 'valet/page.tsx' in tfile:
            target = unescape(args.get('TargetContent', ''))
            
            with open('frontend/src/app/valet/page.tsx', 'r', encoding='utf-8') as src:
                content = src.read().replace('\r\n', '\n')
            
            if target in content:
                print(f"Target {count} FOUND")
            else:
                print(f"Target {count} NOT FOUND")
                print("TARGET PREVIEW: ", repr(target[:50]))
            count += 1
