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
        
        tool_calls = data['tool_calls']
        if isinstance(tool_calls, str):
            try: tool_calls = json.loads(tool_calls)
            except: continue
            
        for call in tool_calls:
            args = call.get('args', {})
            if isinstance(args, str):
                try: args = json.loads(args)
                except: args = {}
                
            tfile = args.get('TargetFile', '')
            if isinstance(tfile, str) and tfile.startswith('\"') and tfile.endswith('\"'):
                try: tfile = json.loads(tfile)
                except: pass
                
            if not tfile or '.gemini' in tfile: continue
            
            target = args.get('TargetContent', '')
            if isinstance(target, str) and target.startswith('\"') and target.endswith('\"'):
                try: target = json.loads(target, strict=False)
                except: pass
                
            replacement = args.get('ReplacementContent', '')
            if isinstance(replacement, str) and replacement.startswith('\"') and replacement.endswith('\"'):
                try: replacement = json.loads(replacement, strict=False)
                except: pass
                
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
                    print(f'Error processing {tfile}: {e}')

print(f'Recovered {count} edits.')
