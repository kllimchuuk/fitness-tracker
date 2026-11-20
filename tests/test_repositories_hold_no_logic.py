import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOGIC = (
    ast.If,
    ast.IfExp,
    ast.Match,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.BoolOp,
    ast.Try,
    ast.TryStar,
)
REPOSITORIES = sorted(
    path
    for path in ROOT.glob("*/repositor*/**/*.py")
    if path.name not in {"__init__.py", "base.py"} and "migrations" not in path.parts
)


def test_the_repositories_are_found() -> None:
    assert {path.stem for path in REPOSITORIES} >= {"session", "weight_tracker"}


@pytest.mark.parametrize("path", REPOSITORIES, ids=lambda path: path.stem)
def test_a_repository_runs_queries_and_holds_no_logic(path: Path) -> None:
    """Branches, loops and defaults belong in the service that calls the repository."""
    tree = ast.parse(path.read_text())

    found = [f"line {node.lineno}: {type(node).__name__}" for node in ast.walk(tree) if isinstance(node, LOGIC)]

    assert found == []


@pytest.mark.parametrize("path", REPOSITORIES, ids=lambda path: path.stem)
def test_a_repository_takes_plain_arguments(path: Path) -> None:
    """No `*`, `*args`, `**kwargs`, keyword-only markers or `**` unpacking."""
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Starred):
            found.append(f"line {node.lineno}: * unpacking")
        elif isinstance(node, ast.arguments) and (node.vararg or node.kwarg or node.kwonlyargs):
            first = node.vararg or node.kwarg or node.kwonlyargs[0]
            found.append(f"line {first.lineno}: *args, **kwargs or keyword-only")
        elif isinstance(node, ast.keyword) and node.arg is None:
            found.append(f"line {node.value.lineno}: ** unpacking")

    assert found == []
