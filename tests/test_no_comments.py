import io
import os
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "migrations",
    "node_modules",
    "staticfiles",
    ".pytest_cache",
    ".ruff_cache",
}
CODES = r"[A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*"
DIRECTIVE = re.compile(
    rf"#\s*(?:noqa(?::\s*{CODES})?|type:\s*ignore(?:\[[\w,\s-]+\])?|pragma:\s*no (?:cover|branch)"
    rf"|fmt:\s*(?:on|off|skip)|isort:\s*(?:on|off|skip)|ruff:\s*(?:noqa(?::\s*{CODES})?|isort:\s*skip_file))\s*"
)


def python_files() -> list[Path]:
    found = []
    for directory, subdirectories, names in os.walk(ROOT):
        subdirectories[:] = [name for name in subdirectories if name not in SKIPPED_DIRECTORIES]
        found.extend(Path(directory, name) for name in names if name.endswith(".py"))
    return sorted(found)


def test_the_python_files_are_found() -> None:
    relative = {str(path.relative_to(ROOT)) for path in python_files()}

    assert {"manage.py", "config/settings.py", ".claude/hooks/reviewer_readonly.py"} <= relative


@pytest.mark.parametrize("path", python_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_python_code_has_no_comments(path: Path) -> None:
    """Why something exists goes to SPEC or DECISIONS; tool directives stay."""
    found = [
        f"line {token.start[0]}: {token.string}"
        for token in tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
        if token.type == tokenize.COMMENT and not token.string.startswith("#!") and not DIRECTIVE.fullmatch(token.string)
    ]

    assert found == []


@pytest.mark.parametrize(
    ("comment", "allowed"),
    [
        ("# noqa", True),
        ("# noqa: E501", True),
        ("# type: ignore[attr-defined]", True),
        ("# pragma: no cover", True),
        ("# fmt: off", True),
        ("# noqa: E501, F401", True),
        ("# isort: skip", True),
        ("# pragmatically chosen", False),
        ("# type: ignored because the ORM returns Any", False),
        ("# fmt: offset by one", False),
        ("# pragma: no cover since the branch is unreachable", False),
        ("# noqa: the reason is X", False),
        ("# noqa-free on purpose", False),
        ("# type: because the ORM returns Any", False),
        ("# explains why", False),
    ],
)
def test_only_real_tool_directives_are_allowed(comment: str, allowed: bool) -> None:
    assert bool(DIRECTIVE.fullmatch(comment)) is allowed
