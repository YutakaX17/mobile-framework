from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOTS = [
    "backend",
    "contracts",
    "tools",
]

EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def iter_python_files() -> list[Path]:
    python_files: list[Path] = []
    for source_root in SOURCE_ROOTS:
        root = ROOT / source_root
        if not root.is_dir():
            raise AssertionError(f"Missing Python source root: {source_root}")
        for path in root.rglob("*.py"):
            if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
                continue
            python_files.append(path)
    return sorted(python_files)


def validate_python_file(path: Path) -> None:
    relative_path = path.relative_to(ROOT)
    try:
        source = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"{relative_path} is not valid UTF-8: {exc}") from exc

    try:
        ast.parse(source, filename=str(relative_path))
    except SyntaxError as exc:
        raise AssertionError(f"{relative_path} has invalid syntax: {exc}") from exc


def main() -> int:
    try:
        python_files = iter_python_files()
        for path in python_files:
            validate_python_file(path)
    except AssertionError as exc:
        print(f"Python source validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Python source validation passed for {len(python_files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
