import os
import ast
import importlib
import pytest
from fastapi.routing import APIRoute
from app.main import app

TARGET_ROUTERS = ['products', 'returns', 'order_feedback']

def test_zero_category_a_get_calls_in_catalog_routers():
    for mod_name in TARGET_ROUTERS:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'routers', f'{mod_name}.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)
        cat_a_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                    lines = code.splitlines()
                    line_text = lines[node.lineno - 1].strip()
                    if not line_text.startswith('@router.get'):
                        cat_a_calls.append((node.lineno, line_text))

        assert len(cat_a_calls) == 0, f'Got Category A calls in {file_path}: {cat_a_calls}'

def test_catalog_routers_import_cleanly():
    for mod_name in TARGET_ROUTERS:
        mod = importlib.import_module(f'app.routers.{mod_name}')
        assert hasattr(mod, 'router'), f'Router module {mod_name} must export a router'
        assert len(mod.router.routes) > 0, f'Router {mod_name} must have defined routes'

def test_catalog_routers_openapi_paths_present():
    schema = app.openapi()
    paths = schema.get('paths', {})

    product_paths = [p for p in paths if '/products' in p]
    return_paths = [p for p in paths if '/returns' in p]
    feedback_paths = [p for p in paths if '/order-feedback' in p]

    assert len(product_paths) >= 5, f'Expected >= 5 product paths, got {len(product_paths)}'
    assert len(return_paths) >= 5, f'Expected >= 5 return paths, got {len(return_paths)}'
    assert len(feedback_paths) >= 2, f'Expected >= 2 order-feedback paths, got {len(feedback_paths)}'