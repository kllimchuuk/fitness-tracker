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
DIRECTIVE = re.compile(
    r"#\s*(?:noqa(?::|\s*$)|type:\s*ignore|pragma:\s*no (?:cover|branch)|fmt:\s*(?:on|off|skip)"
    r"|isort:\s*(?:on|off|skip)|ruff:\s*(?:noqa|isort|disable|enable))"
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
        if token.type == tokenize.COMMENT and not token.string.startswith("#!") and not DIRECTIVE.match(token.string)
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
        ("# pragmatically chosen", False),
        ("# noqa-free on purpose", False),
        ("# type: because the ORM returns Any", False),
        ("# explains why", False),
    ],
)
def test_only_real_tool_directives_are_allowed(comment: str, allowed: bool) -> None:
    assert bool(DIRECTIVE.match(comment)) is allowed
