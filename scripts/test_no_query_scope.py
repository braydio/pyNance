
import ast
import os

PROJECT_DIR = "app"

def is_top_level_query_use(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read(), filename=filepath)

    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.Expr, ast.If)):
            if ast.dump(node).find("query") != -1:
                return True
    return False

def test_no_model_query_at_module_scope():
    violations = []
    for root, _, files in os.walk(PROJECT_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                if is_top_level_query_use(path):
                    violations.append(path)

    assert not violations, f"Model.query used at top-level in: {violations}"
