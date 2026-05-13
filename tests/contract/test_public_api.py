"""Contract: every symbol in API.md must be in ``opstree.__all__`` and vice versa."""

from __future__ import annotations

import ast
import re
from pathlib import Path


_ROOT = Path(__file__).parents[2]
_API_MD = _ROOT / "docs" / "API.md"
_INIT_PY = _ROOT / "src" / "opstree" / "__init__.py"


def _parse_all_from_init() -> set[str]:
    """Parse ``__all__`` list from ``opstree/__init__.py`` statically."""
    text = _INIT_PY.read_text()
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return {
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant)
                    }
    return set()


def _parse_api_md_functions() -> set[str]:
    """Extract public Python identifiers mentioned in API.md code blocks."""
    text = _API_MD.read_text()
    code_blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)

    names: set[str] = set()
    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("from opstree import"):
                rest = line.removeprefix("from opstree import").strip()
                rest = rest.split("#")[0].strip()
                rest = rest.removeprefix("(").removesuffix(")").strip()
                for token in rest.split(","):
                    token = token.strip()
                    if token and not token.startswith("#"):
                        names.add(token)
    return names


def test_public_api_matches_docs():
    """Every symbol in ``opstree.__all__`` must be documented.
    Every symbol listed in API.md import blocks must be in ``__all__``."""
    documented = _parse_api_md_functions()
    public = _parse_all_from_init()

    missing_in_docs = public - documented
    missing_in_code = documented - public

    assert not missing_in_docs, f"Missing from API.md: {missing_in_docs}"
    assert not missing_in_code, f"Missing from opstree.__all__: {missing_in_code}"
