"""`proven` imports nothing but the standard library and itself — checked by AST.

The optional Claude extractor imports the `anthropic` SDK lazily, inside the
function that needs it, so that the package installs and runs with no third-party
dependency at all. That lazy import is the single allowed exception, and it is
named here rather than tolerated silently.
"""
import ast
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
LAZY_ALLOWED = {("llm.py", "anthropic")}


def imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node, alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node, node.module.split(".")[0]


def test_only_stdlib_and_self():
    offenders = []
    for path in sorted(PACKAGE.glob("*.py")):
        for node, root in imports(path):
            if root == "proven" or root in sys.stdlib_module_names or root == "__future__":
                continue
            if (path.name, root) in LAZY_ALLOWED and node.col_offset > 0:
                continue        # imported inside a function, not at module load
            offenders.append(f"{path.name}:{node.lineno} imports {root}")
    assert not offenders, offenders
