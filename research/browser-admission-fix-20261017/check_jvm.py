import ast
from pathlib import Path

runner = Path(__file__).with_name('check_followup.py')
tree = ast.parse(runner.read_text())
selected = []
include = True
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'overlay' for target in node.targets):
        include = False
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'classes' for target in node.targets):
        include = True
    if include:
        selected.append(node)
exec(compile(ast.Module(body=selected, type_ignores=[]), str(runner), 'exec'))
