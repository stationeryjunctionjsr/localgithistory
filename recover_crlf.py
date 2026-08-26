import json

def unescape(s):
    if isinstance(s, str) and s.startswith('"'):
        s = s[1:-1]
        s = s.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t').replace('\\\\', '\\')
    return s.replace('\r\n', '\n')

count = 0
with open('transcript_edits.jsonl', 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: data = json.loads(line)
        except: continue
        if 'tool_calls' not in data: continue
        for call in data['tool_calls']:
            args = call.get('args', {})
            tfile = unescape(args.get('TargetFile', ''))
            
            if not tfile or '.gemini' in tfile: continue
            if 'schemas.py' in tfile or 'returns.py' in tfile: continue
            
            target = unescape(args.get('TargetContent', ''))
            replacement = unescape(args.get('ReplacementContent', ''))
            
            if call['name'] == 'replace_file_content':
                try:
                    with open(tfile, 'r', encoding='utf-8') as src:
                        content = src.read().replace('\r\n', '\n')
                        
                    if target in content:
                        new_content = content.replace(target, replacement)
                        with open(tfile, 'w', encoding='utf-8') as out:
                            out.write(new_content)
                        print(f'Replaced target in {tfile}')
                        count += 1
                    else:
                        pass
                except Exception as e:
                    print(f'Error {tfile}: {e}')
print(f'Recovered {count} edits.')
