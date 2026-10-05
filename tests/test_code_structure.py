"""Small structural checks that prevent accidental duplicate definitions."""

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "build", "dist", "_internal"}


def _python_files():
    return sorted(
        path
        for path in ROOT.rglob("*.py")
        if not any(part in IGNORED_PARTS for part in path.parts)
    )


def _duplicate_names(nodes):
    seen = set()
    duplicates = set()
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                duplicates.add(node.name)
            seen.add(node.name)
    return duplicates


class CodeStructureTests(unittest.TestCase):
    def test_no_duplicate_module_or_class_definitions(self):
        problems = []

        for path in _python_files():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as error:
                problems.append(f"{path}: syntax error: {error}")
                continue

            duplicates = _duplicate_names(tree.body)
            if duplicates:
                problems.append(
                    f"{path}: duplicate module definitions: "
                    + ", ".join(sorted(duplicates))
                )

            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                duplicates = _duplicate_names(node.body)
                if duplicates:
                    problems.append(
                        f"{path}: class {node.name} has duplicate definitions: "
                        + ", ".join(sorted(duplicates))
                    )

        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
