import ast
import re
import glob

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0].capitalize() + ''.join(x.capitalize() for x in components[1:])

class Modifier:
    def __init__(self, source):
        self.source_lines = source.splitlines()
        self.imports = set()

    def get_model_name(self, repo_name):
        base = repo_name.replace('_repository', '')
        if base == 'delivery_charge': return 'DeliveryChargeInternalCreate'
        if base == 'delivery_slot': return 'DeliverySlotConfigInternalCreate'
        if base == 'promo_strip': return 'PromoStripsInternalCreate'
        if base == 'banner': return 'BannerInternalCreate'
        if base == 'sub_order': return 'SubOrderInternalCreate'
        if base == 'valet_payout': return 'ValetPayoutInternalCreate'
        if base == 'seller_payout': return 'SellerPayoutInternalCreate'
        if base == 'coupon': return 'CouponInternalCreate'
        if base == 'notification': return 'NotificationInternalCreate'
        if base == 'order': return 'OrderInternalCreate'
        if base == 'return_request': return 'ReturnRequestInternalCreate'
        if base == 'product': return 'ProductInternalCreate'
        if base == 'seller': return 'SellerInternalCreate'
        if base == 'user': return 'UserInternalCreate'
        return to_camel_case(base) + "InternalCreate"

    def modify(self):
        tree = ast.parse('\n'.join(self.source_lines))
        replacements = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id.endswith('_repository'):
                        if node.func.attr in ('create', 'update', 'update_status'):
                            if node.args and isinstance(node.args[0], ast.Dict):
                                arg = node.args[0]
                                model_name = self.get_model_name(node.func.value.id)
                                self.imports.add(model_name)
                                replacements.append((arg.lineno, arg.col_offset, f"{model_name}(**{{'_id': __import__('uuid').uuid4().hex, **"))
                                replacements.append((arg.end_lineno, arg.end_col_offset, "})"))
        
        replacements.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for lineno, col, text in replacements:
            line = self.source_lines[lineno - 1]
            self.source_lines[lineno - 1] = line[:col] + text + line[col:]
            
        return '\n'.join(self.source_lines)

for f in glob.glob('tests/test_*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        src = file.read()
    try:
        mod = Modifier(src)
        new_src = mod.modify()
        
        if mod.imports:
            imports_list = list(mod.imports)
            imp_str = ""
            for imp in imports_list:
                imp_str += f"try:\n    from app.models.daos import {imp}\nexcept ImportError:\n    pass\ntry:\n    from app.models.daos_flat import {imp}\nexcept ImportError:\n    pass\n"
            new_src = imp_str + new_src
            
        new_src = new_src.replace('zone_ids=', 'zoneIds=')
        new_src = new_src.replace('"zone_ids":', '"zoneIds":')
        new_src = new_src.replace("'zone_ids':", "'zoneIds':")

        if new_src != src:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_src)
            print(f"Fixed {f}")
    except Exception as e:
        print(f"Failed {f}: {e}")
