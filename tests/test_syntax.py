"""Compile-check every .py file in the project.

Catches syntax errors introduced by merges before they reach production.
Uses py_compile only — no imports, no side effects.
"""

import os
import py_compile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {
    ".pixi",
    ".git",
    ".claude",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}


def _collect_py_files():
    py_files = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, PROJECT_ROOT)
                py_files.append(pytest.param(full, id=rel))
    return py_files


@pytest.mark.parametrize("filepath", _collect_py_files())
def test_python_file_compiles(filepath):
    py_compile.compile(filepath, doraise=True)
