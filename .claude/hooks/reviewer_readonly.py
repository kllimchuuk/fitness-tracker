#!/usr/bin/env python3
"""PreToolUse hook for the reviewer subagent: let only read-only Bash through.

Claude Code passes the tool call as JSON on stdin. Exit code 2 blocks the call and
shows stderr to the agent. Every command has its own allowlist of flags, so anything
not recognised is blocked, and any failure of the hook itself blocks too. It is
defense in depth on top of the agent's tool list, not a sandbox.
"""

import json
import re
import shlex
import sys

BLOCK = "Blocked by the reviewer read-only hook"

SHELL_SYNTAX = re.compile(r"[;&<>`\\$\n\r{}()*?\[\]!]|(?:^|\s)~")
FILTERS = re.compile(r"(?:head|tail)(?: -n ?\d+| -\d+)?|wc(?: -[lwc])?|sort|uniq(?: -c)?")

ENV_PREFIX = "DB_HOST=localhost "
UV_DIRECTORY = re.compile(r"[\w./-]+")

GIT_READ_ONLY = {"status", "diff", "log", "show", "ls-files", "rev-parse", "merge-base", "blame", "ls-tree"}
GIT_DENIED_LONG = (
    "--output",
    "--ext-diff",
    "--textconv",
    "--no-index",
    "--untracked",
    "--no-exclude-standard",
    "--exclude-standard",
    "--open-files-in-pager",
)
GIT_GREP_FLAGS = {"-n", "-i", "-e", "-F", "-E", "-w", "-l", "-c", "--"}
GIT_BRANCH_FLAGS = {"--show-current", "-a", "-r", "-vv", "--list"}

RUFF_CHECK_FLAGS = {"--quiet", "-q", "--no-cache", "--statistics", "--exit-zero"}
RUFF_FORMAT_FLAGS = {"--check", "--diff", "--quiet", "-q", "--no-cache"}
RUFF_OUTPUT_FORMAT = re.compile(r"--output-format=(?:concise|full|grouped)")

PYTEST_FLAGS = {"-q", "-qq", "-v", "-vv", "-x", "--no-cov", "--collect-only", "--co", "--lf", "-rf", "-rfE"}
PYTEST_VALUE_FLAGS = {"-k", "-m"}
PYTEST_MAXFAIL = re.compile(r"--maxfail=\d+")
PYTEST_TRACEBACKS = {"--tb=short", "--tb=line", "--tb=no"}

DOCKER_CONFIG_FLAGS = {"--quiet", "-q", "--services", "--no-interpolate"}


def deny(reason: str) -> None:
    print(
        f"{BLOCK}: {reason}. The reviewer may only run read-only git commands, "
        "ruff check, ruff format --check, pytest (with --tb=short, --tb=line or --tb=no) and "
        "docker compose ps or config --quiet, optionally piped into head, tail, wc, sort or uniq.",
        file=sys.stderr,
    )
    sys.exit(2)


def check_git_option(argument: str) -> None:
    if argument.startswith("--"):
        name = argument.split("=", 1)[0]
        if name != "--" and any(denied.startswith(name) for denied in GIT_DENIED_LONG):
            deny(f"argument not allowed: {argument!r}")
    elif argument.startswith("-") and re.search("[oO]", argument):
        deny(f"argument not allowed: {argument!r}")


def check_git(tokens: list[str]) -> None:
    subcommand = tokens[1] if len(tokens) > 1 else ""
    arguments = tokens[2:]
    if subcommand in GIT_READ_ONLY:
        for argument in arguments:
            check_git_option(argument)
    elif subcommand == "grep":
        skip = False
        for argument in arguments:
            if skip:
                skip = False
            elif argument in GIT_GREP_FLAGS:
                skip = argument == "-e"
            elif argument.startswith("-"):
                deny(f"git grep flag not allowed: {argument!r}")
    elif subcommand == "branch":
        if len(arguments) > 1 or any(argument not in GIT_BRANCH_FLAGS for argument in arguments):
            deny("only listing branches is allowed")
    else:
        deny(f"git subcommand not allowed: {subcommand!r}")


def check_ruff(tokens: list[str]) -> None:
    subcommand = tokens[0] if tokens else ""
    arguments = tokens[1:]
    if subcommand == "check":
        allowed = RUFF_CHECK_FLAGS
    elif subcommand == "format":
        allowed = RUFF_FORMAT_FLAGS
        if "--check" not in arguments and "--diff" not in arguments:
            deny("ruff format needs --check or --diff")
    else:
        deny(f"ruff subcommand not allowed: {subcommand!r}")
    for argument in arguments:
        if argument.startswith("-") and argument not in allowed and not RUFF_OUTPUT_FORMAT.fullmatch(argument):
            deny(f"argument not allowed: {argument!r}")


def check_pytest(tokens: list[str]) -> None:
    skip = False
    for argument in tokens:
        if skip:
            skip = False
        elif argument.startswith("@"):
            deny(f"argument not allowed: {argument!r}")
        elif argument in PYTEST_VALUE_FLAGS:
            skip = True
        elif (
            argument in PYTEST_FLAGS
            or argument in PYTEST_TRACEBACKS
            or PYTEST_MAXFAIL.fullmatch(argument)
            or not argument.startswith("-")
        ):
            continue
        else:
            deny(f"argument not allowed: {argument!r}")
    if not PYTEST_TRACEBACKS.intersection(tokens):
        deny("pytest needs --tb=short, --tb=line or --tb=no so that tracebacks do not print settings")


def check_docker(tokens: list[str]) -> None:
    if tokens == ["docker", "compose", "ps"]:
        return
    flags = tokens[3:]
    if tokens[:3] == ["docker", "compose", "config"] and len(flags) == 1 and flags[0] in DOCKER_CONFIG_FLAGS:
        return
    deny("docker compose is limited to ps and config with --quiet, --services or --no-interpolate")


def check_uv(tokens: list[str]) -> str:
    rest = tokens[2:]
    if rest[:1] == ["--directory"]:
        directory = rest[1:2]
        if not directory or not UV_DIRECTORY.fullmatch(directory[0]):
            deny("uv --directory needs a plain path")
        rest = rest[2:]
    tool = rest[0] if rest else ""
    if tool == "ruff":
        check_ruff(rest[1:])
    elif tool == "pytest":
        check_pytest(rest[1:])
    else:
        deny(f"uv run target not allowed: {tool!r}")
    return tool


def check_first(first: str) -> None:
    prefixed = first.startswith(ENV_PREFIX)
    if prefixed:
        first = first[len(ENV_PREFIX) :]
    try:
        tokens = shlex.split(first)
    except ValueError:
        deny("unbalanced quotes")

    if tokens[:2] == ["uv", "run"]:
        tool = check_uv(tokens)
    elif prefixed:
        deny("an environment prefix is allowed only on uv run pytest")
    elif tokens[:1] == ["git"]:
        check_git(tokens)
        return
    elif tokens[:1] == ["docker"]:
        check_docker(tokens)
        return
    else:
        deny(f"command not on the allowlist: {first!r}")
    if prefixed and tool != "pytest":
        deny("an environment prefix is allowed only on uv run pytest")


def check(command: str) -> None:
    command = command.strip()
    if not command:
        deny("empty command")
    if SHELL_SYNTAX.search(command):
        deny("shell syntax that can chain or redirect")

    first, *filters = (segment.strip() for segment in command.split("|"))
    for segment in filters:
        if not FILTERS.fullmatch(segment):
            deny(f"pipe target not on the allowlist: {segment!r}")
    check_first(first)


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "Bash":
            return
        command = event.get("tool_input", {}).get("command")
        if not isinstance(command, str):
            deny("missing command")
        check(command)
    except Exception:
        deny("the hook could not check this call")


if __name__ == "__main__":
    main()
