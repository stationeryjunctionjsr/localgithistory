import json, os, subprocess

missing = 0
present = 0
with open('transcript_edits.jsonl', encoding='utf-8-sig') as f:
    for line in f:
        try:
            d = json.loads(line)
            tool_calls = d.get('tool_calls', [])
            if not tool_calls: continue
            tc = tool_calls[0]
            args = tc.get('args', {})
            tf = args.get('TargetFile', '').strip('\"\'')
            if not tf: continue
            
            norm_tf = os.path.normpath(tf)
            rel_path = os.path.relpath(norm_tf, r'c:\Ecommerce app').replace('\\', '/')
            repl = args.get('ReplacementContent', '')
            
            # Unescape string if it starts and ends with quotes
            if repl.startswith('"') and repl.endswith('"'):
                try:
                    repl = json.loads(repl)
                except:
                    pass
            
            res = subprocess.run(['git', 'show', 'HEAD:' + rel_path], capture_output=True, text=True, encoding='utf-8')
            if res.returncode != 0:
                print(f"File {rel_path} not in HEAD")
                missing += 1
                continue
                
            head_content = res.stdout
            lines = [l.strip() for l in repl.splitlines() if len(l.strip()) > 15]
            miss = [l for l in lines if l not in head_content]
            
            if lines and len(miss) / len(lines) > 0.3:
                print(f"MISSING IN HEAD: {rel_path} - {tc.get('name')}")
                missing += 1
            else:
                present += 1
        except Exception as e:
            pass

print(f"\\nTotal in HEAD: present={present}, missing={missing}")
