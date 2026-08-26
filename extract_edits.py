import json

cid = "bb9a944b-16f1-4cea-a212-aeb6d6407126"
log_path = rf'C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\{cid}\.system_generated\logs\transcript_full.jsonl'

with open('extracted_edits.txt', 'w', encoding='utf-8') as out_f:
    with open(log_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            try: data = json.loads(line)
            except: continue
            if 'tool_calls' not in data: continue
            
            tool_calls = data['tool_calls']
            if isinstance(tool_calls, str):
                try: tool_calls = json.loads(tool_calls)
                except: continue
                
            for call in tool_calls:
                if call['name'] not in ('replace_file_content', 'multi_replace_file_content'):
                    continue
                
                args = call.get('args', {})
                if isinstance(args, str):
                    try: args = json.loads(args)
                    except: continue
                    
                tfile = args.get('TargetFile', '')
                if not tfile or '.gemini' in tfile:
                    continue
                    
                desc = args.get('Description', args.get('Instruction', call['name']))
                out_f.write(f"\n====================================\n")
                out_f.write(f"FILE: {tfile}\n")
                out_f.write(f"DESC: {desc}\n")
                
                chunks = []
                if call['name'] == 'replace_file_content':
                    chunks = [{'TargetContent': args.get('TargetContent',''), 'ReplacementContent': args.get('ReplacementContent','')}]
                elif call['name'] == 'multi_replace_file_content':
                    chunks = args.get('ReplacementChunks', [])
                    if isinstance(chunks, str):
                        try: chunks = json.loads(chunks)
                        except: chunks = []
                    
                for i, chunk in enumerate(chunks):
                    out_f.write(f"--- TARGET ---\n{chunk.get('TargetContent', '')}\n")
                    out_f.write(f"--- REPLACEMENT ---\n{chunk.get('ReplacementContent', '')}\n")
