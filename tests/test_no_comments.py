import io
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = ("authentication", "tracker", "config", "tests", ".claude/hooks")
DIRECTIVES = ("noqa", "type:", "pragma", "fmt:", "isort:", "ruff:")


def python_files() -> list[Path]:
    return sorted(
        path
        for directory in CODE
        for path in (ROOT / directory).rglob("*.py")
        if not {".venv", "__pycache__", "migrations"} & set(path.parts)
    )


@pytest.mark.parametrize("path", python_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_python_code_has_no_comments(path: Path) -> None:
    """Why something exists goes to SPEC or DECISIONS; tool directives stay."""
    found = [
        f"line {token.start[0]}: {token.string}"
        for token in tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
        if token.type == tokenize.COMMENT
        and not token.string.startswith("#!")
        and not token.string.lstrip("# ").startswith(DIRECTIVES)
    ]

    assert found == []
