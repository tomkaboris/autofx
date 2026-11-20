"""Regression test: Vehicle widgets must exist before their first use.

Uses AST so it runs without a display server.
"""
import ast
from pathlib import Path
import unittest


class VehicleUiStartupTests(unittest.TestCase):
    def test_identity_widgets_not_accessed_before_build_ui(self):
        source = Path(__file__).resolve().parents[1] / "desktop.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        window = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AutoFX")
        constructor = next(n for n in window.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        build_calls = [
            n.lineno for n in ast.walk(constructor)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "self" and n.func.attr == "build_ui"
        ]
        self.assertEqual(len(build_calls), 1)
        first_build = build_calls[0]
        for node in ast.walk(constructor):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "self" and node.attr in (
                    "identity_fields", "identity_pids", "identity_note"
                ):
                    self.assertGreater(node.lineno, first_build)


if __name__ == "__main__":
    unittest.main()
