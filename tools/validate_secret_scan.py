from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PARTS = {
    ".git",
    ".gradle",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "playwright-report",
    "test-results",
}

MAX_FILE_BYTES = 1_000_000

ALLOWED_PLACEHOLDER_VALUES = {
    "dev-only-placeholder-change-before-production",
}


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]


SECRET_PATTERNS = [
    SecretPattern(
        "private-key-block",
        re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    ),
    SecretPattern("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    SecretPattern(
        "github-token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b"),
    ),
    SecretPattern(
        "slack-token",
        re.compile(r"\bxox(?:a|b|p|r|s)-[A-Za-z0-9-]{20,}\b"),
    ),
    SecretPattern(
        "stripe-live-secret-key",
        re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
    ),
    SecretPattern(
        "long-secret-assignment",
        re.compile(
            r"""(?ix)
            \b
            (?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|
               refresh[_-]?token|auth[_-]?token|private[_-]?key|password)
            \b
            \s*[:=]\s*
            ["']?[A-Za-z0-9_./+=-]{24,}["']?
            """
        ),
    ),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return sorted(ROOT / path for path in paths if path)


def should_scan(path: Path) -> bool:
    relative_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDED_PARTS for part in relative_parts):
        return False
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        return False
    return True


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def scan_file(path: Path) -> list[str]:
    text = read_text(path)
    if text is None:
        return []

    relative = path.relative_to(ROOT).as_posix()
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(placeholder in line for placeholder in ALLOWED_PLACEHOLDER_VALUES):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.regex.search(line):
                findings.append(f"{relative}:{line_number}: {pattern.name}")
    return findings


def main() -> int:
    findings: list[str] = []
    try:
        for path in tracked_files():
            if should_scan(path):
                findings.extend(scan_file(path))
    except subprocess.CalledProcessError as exc:
        print(f"Secret scan failed to list tracked files: {exc}", file=sys.stderr)
        return 1

    if findings:
        print("Secret scan found high-confidence findings:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
