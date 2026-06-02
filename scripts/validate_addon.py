from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "KMTOOLS_"


def iter_python_files():
    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in path.parts:
            yield path


def validate_class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {getattr(base, "attr", "") for base in node.bases}
        blender_bases = {"Operator", "Panel", "PropertyGroup", "Menu", "Header", "UIList"}
        if base_names & blender_bases and not node.name.startswith(PREFIX):
            errors.append(f"{path.relative_to(ROOT)}:{node.lineno} class {node.name} must start with {PREFIX}")
    return errors


def main() -> int:
    errors = []
    for path in iter_python_files():
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        errors.extend(validate_class_names(path))

    if errors:
        for error in errors:
            print(error)
        return 1

    print("Addon validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())