import os, ast, re

files = [
    'backend/app/routers/referrals.py', 'backend/app/routers/returns.py', 'backend/app/routers/schemes.py',
    'backend/app/routers/seller_availability.py', 'backend/app/routers/seller_requests.py', 'backend/app/routers/tracking.py',
    'backend/app/routers/users.py', 'backend/app/routers/valet_availability.py', 'backend/app/routers/valet_payout.py',
    'backend/app/routers/version.py', 'backend/app/routers/wishlist.py', 'backend/app/scripts/update_customer_ids.py',
    'backend/app/services/email_service.py', 'backend/app/services/push_notification_service.py', 'backend/app/services/report_service.py',
    'backend/app/utils/auth.py', 'backend/app/utils/cache.py', 'backend/app/utils/cookies.py', 'backend/app/utils/device.py',
    'backend/app/utils/email_otp.py', 'backend/app/utils/error_handler.py', 'backend/app/utils/file_storage.py',
    'backend/app/utils/invoice_generator.py', 'backend/app/utils/logger.py', 'backend/app/utils/maintenance.py',
    'backend/app/utils/otp.py', 'backend/app/utils/product_variations.py'
]

def process_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    def replace_get(text):
        res = []
        i = 0
        while i < len(text):
            idx = text.find('.get(', i)
            if idx == -1:
                res.append(text[i:])
                break
            prefix = text[max(0, idx-20):idx]
            if prefix.endswith('router') or prefix.endswith('app') or prefix.endswith('requests') or prefix.endswith('os.environ') or prefix.endswith('request.headers'):
                res.append(text[i:idx+5])
                i = idx + 5
                continue
                
            obj_end = idx
            obj_start = idx - 1
            brackets = 0
            while obj_start >= 0:
                c = text[obj_start]
                if c == ']': brackets += 1
                elif c == '[': brackets -= 1
                elif c == ')': brackets += 1
                elif c == '(': brackets -= 1
                elif brackets == 0 and not (c.isalnum() or c in '_.\"\'{}[]'):
                    break
                obj_start -= 1
            obj_start += 1
            obj = text[obj_start:obj_end]
            
            arg_start = idx + 5
            arg_end = arg_start
            parens = 1
            while arg_end < len(text):
                c = text[arg_end]
                if c == '(': parens += 1
                elif c == ')': parens -= 1
                if parens == 0:
                    break
                arg_end += 1
                
            args_str = text[arg_start:arg_end]
            
            args = []
            cur_arg = []
            in_quote = False
            quote_char = None
            p = 0
            for c in args_str:
                if in_quote:
                    cur_arg.append(c)
                    if c == quote_char:
                        in_quote = False
                else:
                    if c in '\"\'':
                        in_quote = True
                        quote_char = c
                        cur_arg.append(c)
                    elif c == '(':
                        p += 1
                        cur_arg.append(c)
                    elif c == ')':
                        p -= 1
                        cur_arg.append(c)
                    elif c == ',' and p == 0:
                        args.append(''.join(cur_arg).strip())
                        cur_arg = []
                    else:
                        cur_arg.append(c)
            args.append(''.join(cur_arg).strip())
            
            if len(args) == 1:
                key = args[0]
                default = 'None'
            elif len(args) == 2:
                key = args[0]
                default = args[1]
            else:
                res.append(text[i:idx+5])
                i = idx + 5
                continue
            
            replacement = f'{obj}[{key}] if {key} in {obj} else {default}'
            
            res.append(text[i:obj_start])
            res.append(replacement)
            
            i = arg_end + 1

        return ''.join(res)
    
    new_content = replace_get(content)
    # .model_dump()
    new_content = re.sub(r'\.model_dump\((.*?)\)', r'.__dict__', new_content)
    new_content = new_content.replace('.model_dump()', '.__dict__')
    
    # dict() -> {}
    # re.sub dictionary with args
    new_content = re.sub(r'\bdict\((.*?)\)', r'{\1}', new_content)
    new_content = new_content.replace('dict()', '{}')
    
    # row_to_dict
    new_content = new_content.replace('row_to_dict', '_map_to_schema')
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
for f in files:
    try:
        process_file(f)
    except Exception as e:
        print(f'Error processing {f}: {e}')
print("Done!")
