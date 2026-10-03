import sys
import io
import ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open("app/services/order_service.py", "r", encoding="utf-8") as f:
    text = f.read()
class ReturnVisitor(ast.NodeVisitor):
    def visit_Return(self, node):
        print(f"Return at line {node.lineno}: {ast.unparse(node.value) if node.value else 'None'}")
        self.generic_visit(node)
tree = ast.parse(text)
for node in tree.body:
    if isinstance(node, ast.AsyncFunctionDef) and node.name == 'create_order_service':
        ReturnVisitor().visit(node)
