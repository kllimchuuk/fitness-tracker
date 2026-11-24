#!/usr/bin/env python3
"""PreToolUse hook for the main session: enforce the git, docker and secrets rules on parsed tokens.

The deny rules in settings.json match the spelling of a command, so `git add -vf ./.env`,
`git commit --amen` or `git switch --discard` walk past them. This hook splits the command into
simple commands, strips wrappers and git's global options, and judges the real subcommand and its
flags, including abbreviated long options. Exit code 2 blocks the call; a failure of the hook
itself blocks too. It is defense in depth for an agent that follows CLAUDE.md, not a sandbox.
"""

import fnmatch
import json
import os
import re
import shlex
import sys

BLOCK = "Blocked by the main-session guard"

PUNCTUATION = ";&|<>()\n"
SECRET_FILE = re.compile(r"(?:^|[/:=])\.env(?!\.example$)", re.IGNORECASE)
GLOB_CHARS = re.compile(r"[*?\[]")
PIPE_TO_SHELL = re.compile(r"\|&?\s*(?:(?:sudo|env|command|exec)\s+(?:-\S+\s+)*)*(?:bash|sh|zsh|dash)\b")
SUBSTITUTION = re.compile(r"\$\((.*)\)|`([^`]*)`", re.DOTALL)
GLOB_OR_EXPANSION = re.compile(r"[*?\[\]{}$`~]")
PARENT_PATH = re.compile(r"(?:^|/)\.\.(?:/|$)")
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
MIN_OPTION_LENGTH = 3

WRAPPERS = {"env", "command", "sudo", "nohup", "time", "exec", "builtin"}
WRAPPER_VALUE_FLAGS = {"-u", "-g", "-C", "-a", "-S", "-h", "-p", "-U", "-n"}
KEYWORDS = {"{", "}", "!", "if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "case", "esac"}
RUNNERS = {"xargs", "find", "watch", "nice", "timeout"}
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(?P<quote>['\"]?)(?P<word>[\w-]+)(?P=quote)")
INTERPRETERS = re.compile(r"\b(?:bash|sh|zsh|dash|eval|source)\b")
RISKY_LINE = re.compile(r"(?:^|[\s;&|(])(?:git|docker)\s")
SHELLS = {"bash", "sh", "zsh", "dash"}

GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
GIT_FORCE_LONG = ("--force", "--force-with-lease", "--force-if-includes", "--discard-changes", "--force-create")
GIT_DENIED_SUBCOMMANDS = {
    "push": "the owner pushes",
    "send-pack": "the owner pushes",
    "subtree": "subtree can push",
    "reset": "no reset",
    "update-ref": "it rewrites refs like reset",
    "filter-branch": "it rewrites history",
    "rebase": "no rebase",
    "clean": "no clean",
}
GIT_ADD_DENIED_LONG = (
    "--all",
    "--force",
    "--update",
    "--patch",
    "--interactive",
    "--edit",
    "--pathspec-from-file",
    "--no-ignore-removal",
)
GIT_ADD_DENIED_SHORT = set("Aufpie")
GIT_COMMIT_DENIED_LONG = ("--amend", "--all", "--no-verify")
GIT_COMMIT_DENIED_SHORT = set("an")
GIT_COMMIT_VALUE_SHORT = set("mFcC")
GIT_COMMIT_VALUE_LONG = {
    "--message",
    "--file",
    "--reuse-message",
    "--reedit-message",
    "--author",
    "--date",
    "--cleanup",
    "--template",
    "--fixup",
    "--squash",
    "--trailer",
}
GIT_FORCE_SHORT_SUBCOMMANDS = {"branch": set("DfM"), "switch": set("fC"), "checkout": set("fB")}

DOCKER_COMPOSE_DENIED = {"down", "run", "exec", "rm", "kill"}
DOCKER_DENIED = {"rm", "rmi", "volume", "system", "run", "exec", "kill"}


def deny(reason: str) -> None:
    print(
        f"{BLOCK}: {reason}. CLAUDE.md: stage files by explicit path, never push, amend, reset, rebase or force, "
        "never touch .env, never tear down containers or volumes.",
        file=sys.stderr,
    )
    sys.exit(2)


def abbreviates(argument: str, full: str) -> bool:
    name = argument.split("=", 1)[0]
    return len(name) >= MIN_OPTION_LENGTH and full.startswith(name)


def long_matches(argument: str, names: tuple[str, ...]) -> bool:
    return argument.startswith("--") and any(abbreviates(argument, name) for name in names)


def short_letters(argument: str) -> set[str]:
    if argument.startswith("-") and not argument.startswith("--"):
        return set(argument[1:])
    return set()


def split_commands(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    commands: list[list[str]] = [[]]
    for token in lexer:
        if all(character in PUNCTUATION for character in token):
            commands.append([])
        else:
            commands[-1].append(token)
    return [tokens for tokens in commands if tokens]


def check_add(arguments: list[str], cwd: str) -> None:
    for argument in arguments:
        if argument == "--":
            continue
        if argument.startswith("--"):
            if long_matches(argument, GIT_ADD_DENIED_LONG):
                deny(f"git add option not allowed: {argument!r}")
        elif argument.startswith("-") and len(argument) > 1:
            if short_letters(argument) & GIT_ADD_DENIED_SHORT:
                deny(f"git add option not allowed: {argument!r}")
        else:
            check_add_path(argument, cwd)


def check_add_path(path: str, cwd: str) -> None:
    if not path.strip("./"):
        deny("git add of the whole tree is not allowed")
    if path.startswith(":") or GLOB_OR_EXPANSION.search(path) or PARENT_PATH.search(path):
        deny(f"git add needs a plain file path, got {path!r}")
    if os.path.isdir(os.path.join(cwd, path)):
        deny(f"git add needs file paths, {path!r} is a directory")


def short_cluster_takes_next_value(argument: str) -> bool:
    letters = argument[1:]
    for position, letter in enumerate(letters):
        if letter in GIT_COMMIT_DENIED_SHORT:
            deny(f"git commit option not allowed: {argument!r}")
        if letter in GIT_COMMIT_VALUE_SHORT:
            return position == len(letters) - 1
    return False


def check_commit(arguments: list[str]) -> None:
    skip = False
    for argument in arguments:
        if skip:
            skip = False
        elif argument.startswith("--") and argument != "--":
            if long_matches(argument, GIT_COMMIT_DENIED_LONG):
                deny(f"git commit option not allowed: {argument!r}")
            skip = argument in GIT_COMMIT_VALUE_LONG
        elif argument.startswith("-") and argument != "--" and len(argument) > 1:
            skip = short_cluster_takes_next_value(argument)
        else:
            deny(f"git commit takes no paths, stage them first: {argument!r}")


def check_force(subcommand: str, arguments: list[str]) -> None:
    denied_short = GIT_FORCE_SHORT_SUBCOMMANDS.get(subcommand, set())
    for argument in arguments:
        if argument == "--":
            return
        if long_matches(argument, GIT_FORCE_LONG):
            deny(f"force option not allowed: {argument!r}")
        if short_letters(argument) & denied_short:
            deny(f"force option not allowed: {argument!r}")
    if subcommand == "branch" and any(long_matches(argument, ("--delete",)) for argument in arguments):
        deny("deleting branches is not allowed")


def check_git(tokens: list[str], cwd: str) -> None:
    index = 1
    while index < len(tokens) and tokens[index].startswith("-"):
        option = tokens[index]
        value = tokens[index + 1] if index + 1 < len(tokens) else ""
        if option.startswith("--config-env") or (option == "-c" and value.lower().startswith("alias.")):
            deny("git aliases are not allowed")
        if option.lower().startswith("-calias."):
            deny("git aliases are not allowed")
        index += 2 if option in GIT_GLOBAL_WITH_VALUE else 1
    subcommand = tokens[index] if index < len(tokens) else ""
    arguments = tokens[index + 1 :]
    if subcommand == "stage":
        subcommand = "add"

    if subcommand in GIT_DENIED_SUBCOMMANDS:
        deny(f"git {subcommand} is not allowed ({GIT_DENIED_SUBCOMMANDS[subcommand]})")
    if subcommand == "add":
        check_add(arguments, cwd)
    elif subcommand == "commit":
        check_commit(arguments)
    elif subcommand == "config" and any(argument.lower().startswith("alias.") for argument in arguments):
        deny("git aliases are not allowed")
    elif subcommand == "pull" and any(
        long_matches(argument, ("--rebase",)) or "r" in short_letters(argument) for argument in arguments
    ):
        deny("git pull --rebase is not allowed")
    check_force(subcommand, arguments)


def check_docker(tokens: list[str]) -> None:
    words = [token for token in tokens[1:] if not token.startswith("-")]
    if "compose" in words:
        rest = words[words.index("compose") + 1 :]
        denied = DOCKER_COMPOSE_DENIED
    elif os.path.basename(tokens[0]) == "docker-compose":
        rest = words
        denied = DOCKER_COMPOSE_DENIED
    else:
        rest = words
        denied = DOCKER_DENIED
    for word in rest:
        if word in denied:
            deny(f"docker {word} is not allowed")


def names_secret_file(token: str) -> bool:
    if SECRET_FILE.search(token):
        return True
    name = re.split(r"[/:=]", token)[-1]
    return name.startswith(".") and bool(GLOB_CHARS.search(name)) and fnmatch.fnmatchcase(".env", name.lower())


def strip_prefixes(tokens: list[str]) -> list[str]:
    while tokens:
        if ASSIGNMENT.match(tokens[0]):
            if tokens[0].upper().startswith("GIT_CONFIG"):
                deny("git configuration through the environment is not allowed")
            tokens = tokens[1:]
        elif tokens[0] in KEYWORDS:
            tokens = tokens[1:]
        elif tokens[0] in WRAPPERS:
            tokens = tokens[1:]
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[2:] if tokens[0] in WRAPPER_VALUE_FLAGS else tokens[1:]
        else:
            break
    return tokens


def check_runner(tokens: list[str], cwd: str) -> None:
    for position, token in enumerate(tokens):
        if token in {"git", "docker"}:
            following = tokens[position + 1 :]
            if not [word for word in following if not word.startswith("-")]:
                deny("the subcommand of git or docker must be written out, not piped in")
            if "add" in following[:3]:
                deny("git add needs explicit paths, not paths from another command")
            check_simple(tokens[position:], cwd)
            return


def check_simple(tokens: list[str], cwd: str) -> None:
    for token in tokens:
        if names_secret_file(token):
            deny(f"argument names a secrets file: {token!r}")

    tokens = strip_prefixes(tokens)
    if not tokens:
        return

    program = os.path.basename(tokens[0])
    if program in SHELLS:
        for position, token in enumerate(tokens[1:-1], start=1):
            if token.startswith("-") and "c" in token and not token.startswith("--"):
                check_command(tokens[position + 1], cwd)
    elif program == "eval":
        check_command(" ".join(tokens[1:]), cwd)
    elif program in {"source", "."}:
        deny("sourcing a file hides the commands it runs")
    elif program in RUNNERS:
        check_runner(tokens, cwd)
    elif program == "git":
        check_git(tokens, cwd)
    elif program in {"docker", "docker-compose"}:
        check_docker(tokens)


def inside_quote_or_comment(text: str) -> bool:
    frames: list[str] = []
    depths: list[int] = []
    index = 0
    while index < len(text):
        character = text[index]
        mode = frames[-1] if frames else "n"
        if mode == "s":
            if character == "'":
                frames.pop()
        elif mode == "d":
            if character == "\\":
                index += 1
            elif character == '"':
                frames.pop()
            elif text.startswith("$(", index):
                frames.append("c")
                depths.append(0)
                index += 1
        elif character == "\\":
            index += 1
        elif character == "'":
            frames.append("s")
        elif character == '"':
            frames.append("d")
        elif character == "#" and (index == 0 or text[index - 1] in " \t\n;&|("):
            return True
        elif mode == "c" and character == "(":
            depths[-1] += 1
        elif mode == "c" and character == ")":
            if depths[-1] == 0:
                frames.pop()
                depths.pop()
            else:
                depths[-1] -= 1
        index += 1
    return bool(frames) and frames[-1] in {"s", "d"}


def strip_heredocs(command: str, nested: bool) -> tuple[str, str]:
    code: list[str] = []
    expanded: list[str] = []
    pending: list[tuple[str, bool, bool]] = []
    for line in command.split("\n"):
        if pending:
            word, quoted, executed = pending[0]
            if line.strip() == word:
                pending.pop(0)
            elif executed:
                code.append(line)
            elif not quoted:
                expanded.append(line)
            continue
        code.append(line)
        for match in HEREDOC.finditer(line):
            before = "\n".join([*code[:-1], line[: match.start()]])
            if inside_quote_or_comment(before):
                continue
            executed = bool(INTERPRETERS.search(line))
            pending.append((match.group("word"), bool(match.group("quote")), executed))
    if pending and not nested:
        deny("a heredoc is not terminated")
    return "\n".join(code), "\n".join(code + expanded)


def check_command(command: str, cwd: str, nested: bool = False) -> None:
    code, scanned = strip_heredocs(command, nested)
    if PIPE_TO_SHELL.search(code):
        deny("piping text into a shell hides the commands it runs")
    for match in SUBSTITUTION.finditer(scanned):
        check_command(match.group(1) or match.group(2), cwd, nested=True)
    try:
        commands = split_commands(code)
    except ValueError:
        if not nested:
            deny("unbalanced quotes")
        for line in code.splitlines():
            if RISKY_LINE.search(line):
                deny(f"could not parse a git or docker command inside a substitution: {line!r}")
        return
    for tokens in commands:
        check_simple(tokens, cwd)


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "Bash":
            return
        command = event.get("tool_input", {}).get("command")
        if not isinstance(command, str):
            deny("missing command")
        check_command(command, event.get("cwd") or os.getcwd())
    except Exception:
        deny("the hook could not check this call")


if __name__ == "__main__":
    main()
