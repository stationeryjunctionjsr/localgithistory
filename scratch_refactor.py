import ast
import os

def rewrite_ast(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    # Simple text replacements first
    source = source.replace('row_to_dict', '_map_to_schema')
    source = source.replace('dict()', '{}')
    source = source.replace('.model_dump()', '')
    
    class GetTransformer(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            # Check if it is obj.get(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                obj = node.func.value
                args = node.args
                # Do not rewrite if it's fastapi @router.get
                if isinstance(obj, ast.Name) and obj.id == 'router':
                    return node
                
                if len(args) == 1:
                    key = args[0]
                    default = ast.Constant(value=None)
                elif len(args) == 2:
                    key = args[0]
                    default = args[1]
                else:
                    return node
                
                test = ast.Compare(
                    left=key,
                    ops=[ast.In()],
                    comparators=[obj]
                )
                body = ast.Subscript(
                    value=obj,
                    slice=key,
                    ctx=ast.Load()
                )
                orelse = default
                
                return ast.IfExp(test=test, body=body, orelse=orelse)
                
            return node

    tree = ast.parse(source)
    transformer = GetTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    
    new_source = ast.unparse(new_tree)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_source)

rewrite_ast(r"c:\Ecommerce app\backend\app\jobs\valet_timeout_job.py")
rewrite_ast(r"c:\Ecommerce app\backend\app\db\mysql_user_dao.py")
print("Done")
