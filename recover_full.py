import json
import os

count = 0
log_path = r'C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\bb9a944b-16f1-4cea-a212-aeb6d6407126\.system_generated\logs\transcript_full.jsonl'
with open(log_path, 'r', encoding='utf-8-sig') as f:
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
                
            if call['name'] == 'replace_file_content' or call['name'] == 'multi_replace_file_content':
                # handle both single and multi
                chunks = []
                if call['name'] == 'replace_file_content':
                    chunks = [{'TargetContent': target, 'ReplacementContent': replacement}]
                else:
                    chunks = args.get('ReplacementChunks', [])
                    if isinstance(chunks, str):
                        try: chunks = json.loads(chunks)
                        except: chunks = []
                
                try:
                    with open(tfile, 'r', encoding='utf-8') as src:
                        content = src.read()
                    
                    made_change = False
                    for chunk in chunks:
                        tc = chunk.get('TargetContent', '')
                        rc = chunk.get('ReplacementContent', '')
                        if tc in content and tc != rc:
                            content = content.replace(tc, rc)
                            made_change = True
                            count += 1
                        elif tc not in content:
                            print(f"Target not found in {tfile} (Len: {len(tc)})")
                    
                    if made_change:
                        with open(tfile, 'w', encoding='utf-8') as out:
                            out.write(content)
                        print(f'Applied edit to {tfile}')
                except Exception as e:
                    print(f'Error processing {tfile}: {e}')

print(f'Recovered {count} edits.')
