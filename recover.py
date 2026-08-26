import json
import os

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
            tfile = args.get('TargetFile', '')
            if isinstance(tfile, str) and tfile.startswith('"'):
                tfile = json.loads(tfile)
                
            if not tfile or '.gemini' in tfile: continue
            
            target = args.get('TargetContent', '')
            if isinstance(target, str) and target.startswith('"'): 
                target = json.loads(target)
                
            replacement = args.get('ReplacementContent', '')
            if isinstance(replacement, str) and replacement.startswith('"'):
                replacement = json.loads(replacement)
                
            if call['name'] == 'replace_file_content':
                try:
                    with open(tfile, 'r', encoding='utf-8') as src:
                        content = src.read()
                    if target in content:
                        new_content = content.replace(target, replacement)
                        with open(tfile, 'w', encoding='utf-8') as out:
                            out.write(new_content)
                        print(f'Replaced target in {tfile}')
                        count += 1
                    else:
                        print(f'Target not found in {tfile}')
                except Exception as e:
                    print(f'Error {tfile}: {e}')
print(f'Recovered {count} edits.')
