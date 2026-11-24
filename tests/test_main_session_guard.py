import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "main_session_guard.py"
BLOCK_MESSAGE = "Blocked by the main-session guard"


def run_hook(command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {"tool_name": tool_name, "tool_input": {"command": command}, "cwd": str(ROOT)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "command",
    [
        "git status --short",
        "git diff main...HEAD --stat",
        "git log --oneline -5",
        "git switch -c feat/set-logs",
        "git switch main",
        "git branch --show-current",
        "git add tracker/models.py tests/test_env.py",
        "git add -v tracker/models.py",
        "git add -- tracker/models.py",
        "git add .env.example",
        "git commit -m 'feat: log sets per session'",
        "git commit -m \"$(cat <<'EOF'\nfeat: log sets\n\nBody (with parentheses).\nEOF\n)\"",
        "git commit -sm 'fix: x'",
        "git -C . status",
        "git -c color.ui=never log -1",
        "git stash list",
        "uv run pytest --no-cov -q --tb=short",
        "DB_HOST=localhost uv run pytest --no-cov -q",
        "uv run ruff check . && uv run ruff format --check .",
        "docker compose up -d db",
        "docker compose ps",
        "docker compose logs db",
        "cd /Users/nikitaklimcuk/fitness-tracker && git status",
        "git log --format=%s | head -5",
        "grep -rn status authentication",
        "git commit -m 'document the .env rules'",
        "cat docs/SPEC.md",
        "cat >> docs/DECISIONS.md <<'EOF'\nThe old rule matched `git add -vf ./.env` and `git push` as text.\nEOF",
        "cat > notes.md <<'EOF'\ndon't run git add . here\nEOF\ngit status",
        "git commit -m \"$(cat <<'EOF'\nfix: it's fine\n\nMentions .env and git push as words.\nEOF\n)\"",
        "cat <<-'EOF'\n\tgit push\n\tEOF\ngit status",
        "grep -c x <<< git",
    ],
)
def test_normal_work_is_allowed(command: str) -> None:
    result = run_hook(command)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git push",
        "git push origin main",
        "git push --force",
        "git -C . push",
        "git add .",
        "git add ./",
        "git add -A",
        "git add --all",
        "git add --al",
        "git add -u",
        "git add --update",
        "git add -f tracker/models.py",
        "git add -vf ./.env",
        "git add -fv .env",
        "git add --forc tracker/models.py",
        "git add --force tracker/models.py",
        "git add .env",
        "git add ./.env",
        "git add tracker/../.env",
        "git add -- .env",
        "git add :/",
        "git add ':(top)'",
        "git add tracker",
        "git add tracker/",
        "git add tracker/*.py",
        "git add '$(echo .)'",
        "git add --pathspec-from-file=list.txt",
        "git add -p",
        "git commit --amend",
        "git commit --amen -m x",
        "git commit --am",
        "git commit -m x --amend",
        "git commit -a -m x",
        "git commit -am x",
        "git commit --all -m x",
        "git commit --no-verify -m x",
        "git commit -n -m x",
        "git reset --hard",
        "git reset HEAD~1",
        "git rebase main",
        "git rebase -i HEAD~3",
        "git branch -D feat/x",
        "git branch -f feat/x HEAD",
        "git branch --force feat/x HEAD",
        "git branch --delete --forc feat/x",
        "git switch -C feat/x",
        "git switch -f main",
        "git switch --discard main",
        "git switch --discard-changes main",
        "git switch --forc main",
        "git checkout -f main",
        "git clean -fd",
        "git config alias.a 'add -A'",
        "git status && git add .",
        "git status; git add -A",
        "git status\ngit add .",
        "git status | git add .",
        "echo ok && git push",
        "env git add .",
        "command git add .",
        "FOO=1 git add .",
        "sudo git push",
        "bash -c 'git add .'",
        'sh -c "git push"',
        "xargs git add",
        'echo "$(git add .)"',
        "echo `git push`",
        "(git add .)",
        "git -C . add .",
        "git --no-pager add .",
        "cat .env",
        "less ./.env",
        "grep SECRET .env",
        "head -c 100 .env",
        "cp .env /tmp/x",
        "echo x > .env",
        "git diff /dev/null .env",
        "git blame --contents .env README.md",
        "git show HEAD:.env",
        "uv run python manage.py shell --env-file=.env",
        "docker compose down",
        "docker compose down -v",
        "docker compose -f docker-compose.yml down",
        "docker compose run web sh",
        "docker compose exec db psql",
        "docker compose rm -f",
        "docker volume rm fitness-tracker_pgdata",
        "docker system prune -a",
        "docker rm -f db",
        "bash <<'EOF'\ngit add .\nEOF",
        "sh <<EOF\ngit push\nEOF",
        "python3 <<'EOF'\nimport os\nEOF\ncat .env",
        "cat <<EOF\n$(git add .)\nEOF",
        "cat <<'EOF'\nok\nEOF\ngit add .",
        "cat <<'EOF' && git push\nok\nEOF",
        'echo "<<X"\ngit push',
        "cat <<< x\ngit push",
    ],
)
def test_forbidden_work_is_blocked(command: str) -> None:
    result = run_hook(command)

    assert result.returncode == 2, command
    assert BLOCK_MESSAGE in result.stderr


def test_other_tools_are_not_touched() -> None:
    assert run_hook("git push", tool_name="Read").returncode == 0


@pytest.mark.parametrize("stdin", ["", "not json", "[]", '{"tool_name": "Bash", "tool_input": {"command": 5}}'])
def test_unreadable_input_is_blocked(stdin: str) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert BLOCK_MESSAGE in result.stderr


def test_settings_register_the_guard_and_deny_push() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    commands = [
        hook["command"] for entry in settings["hooks"]["PreToolUse"] if entry["matcher"] == "Bash" for hook in entry["hooks"]
    ]

    assert any("main_session_guard.py" in command for command in commands)
    assert "Bash(git push:*)" in settings["permissions"]["deny"]
    assert "Bash(git push:*)" not in settings["permissions"]["ask"]
