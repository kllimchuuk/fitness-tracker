# Decision log

Each entry: date, decision, why, what changed. Newest at the bottom.

## 2026-10-29 — direction of the rework

1. **Keep Django; do not add a FastAPI service.**
   - *Why:* a second framework would duplicate authentication, configuration and deployment for a domain that
     does not need independent scaling. Django already gives the ORM, admin and migrations the project uses.
   - *Changed:* the AI coach will live in an `agent/` app inside the same project.

2. **Adopt Django Ninja for the API.**
   - *Why:* typed Pydantic schemas (already used here), automatic OpenAPI, async endpoints, without leaving Django.
   - *Changed:* nothing yet; the hand-written JSON views are replaced in a later pull request.

3. **The coach is a cascade: deterministic engine first, LLM second.**
   - *Why:* load calculation and progression must be exact and testable; a model is good at explaining and at
     judgement calls (conflicting signals, injuries, plateaus). Calling it only where the engine is unsure
     keeps cost and latency down and makes failure harmless — without an answer the engine's result stands.
   - *Changed:* nothing yet; specified in [`SPEC.md`](SPEC.md).

4. **Deload and plateau advice goes through a state machine with hysteresis.**
   - *Why:* a single bad session must not flip the recommendation back and forth.
   - *Changed:* nothing yet.

5. **Small pull requests, CI as a gate, tests before fixes.**
   - *Why:* the existing suite (~1.4k lines of integration and API tests) is the safety net for refactoring
     authentication and the service layer. Every bug gets a failing test first.
   - *Changed:* GitHub Actions workflow with lint, format check and tests.

6. **Documentation and code comments in English; README and licence are written last.**
   - *Why:* the project is a public portfolio piece, and the README should describe what is actually built.
   - *Changed:* nothing yet. No third-party code is copied into the repository; practices seen in other public
     projects are re-implemented independently.

7. **Repository hygiene fixes found during the audit.**
   - *Why:* `COPY . .` without a `.dockerignore` placed the local `.env` into the image; `pip install .` failed
     on the flat layout; the stylesheet existed only in the git-ignored `staticfiles/`, so a fresh clone had no
     styles.
   - *Changed:* `.dockerignore`; `[tool.setuptools] py-modules = []`; `static/css/base.css` is tracked.

## 2026-11-05 — uv and typed settings

8. **Manage dependencies with uv and a committed `uv.lock`; read configuration through `pydantic-settings`.**
   - *Why:* `pip install .` resolved fresh versions on every build, so CI and the image could differ from a
     developer's machine. `os.getenv` returned raw strings (`DEBUG=False` was truthy) and silently returned
     `None` for a missing `SECRET_KEY`.
   - *Changed:* `config/env.py` declares every variable with a type and fails at start-up when a required one
     is missing; `python-dotenv` is replaced by the `.env` support of `pydantic-settings`. Test dependencies
     moved to a `dev` dependency group. The Docker image installs from the lock file into `/opt/venv`, outside
     the directory docker-compose bind-mounts. CI runs `uv sync --locked`, so a stale lock file fails the build.
     Minimum Python is now 3.13, matching the image and CI.

## 2026-11-10 — Django auth and catalog permissions

9. **Use `django.contrib.auth` (`authenticate`, `login`, `request.user`, `login_required`) instead of a hand-rolled
   `session["user_id"]`.**
   - *Why:* the hand-rolled version ignored `is_active`, did not invalidate sessions on password change, did not
     use the configured password validators and duplicated the login check in about twenty views.
   - *Changed:* logout is POST-only (a GET could log a user out from an image tag); password change calls
     `update_session_auth_hash`; JSON endpoints answer 401 through `ApiLoginRequiredMixin` while HTML views
     redirect to the login page. `?next=` is honoured only for same-host URLs. Emails are unique and looked up
     case-insensitively (`UniqueConstraint(Lower("email"))`, `get_by_natural_key` with `iexact`), because rows
     created before normalisation kept the capitals of their domain.

10. **`Exercise.owner` (nullable FK): `null` is a system exercise, otherwise a private one. Staff (`is_staff`)
    manage system exercises; users manage only their own.**
    - *Why:* the shared catalog was writable by any logged-in user. A separate model for private exercises
      would have duplicated every query and serializer.
    - *Rules:* users see system exercises plus their own (`Exercise.objects.visible_to`). An exercise that is
      invisible to the user is a 404, one that is visible but not theirs to change is a 403. Exercises created
      by staff are always system exercises. Plans accept only visible exercises; sets of a plan and sessions
      can be touched only through the plan's creator.
    - *Migration:* every exercise that existed before `0004_exercise_owner` becomes a system exercise
      (`owner = NULL`).
    - *Deleting:* `ExerciseSet.exercise` is `PROTECT`. An exercise that is part of a plan cannot be deleted (HTML
      shows "used in N plans", the API answers 409) instead of silently disappearing from every user's plans;
      per-set history in PR 3 depends on that.
    - *Privacy:* the exercise detail page lists only the viewer's own plans.

## 2026-11-11 — agent-first working rules

11. **Work by slices with a spec, an invariants list, a read-only reviewer and rules enforced by tests, as in `helpdesk-ai-drafts`.**
    - *Why:* the repository is a portfolio piece that must show how it was built; rules that a test enforces do not depend on anyone remembering them.
    - *Changed:* `CLAUDE.md`; `.claude/` with the `reviewer` subagent, a read-only Bash hook and the skills `spec-slice`, `invariants-check`, `report`; SPEC gets Invariants (I1-I9) and Slices (S0-S8); `tests/test_no_comments.py`, `tests/test_repositories_hold_no_logic.py` and `tests/test_reviewer_readonly_hook.py`.
    - *Differences from helpdesk:* commits carry no `Co-Authored-By` trailer. The agent stages by explicit path and commits locally, as in helpdesk; the owner pushes.

12. **The no-comments guard skips `migrations/`.**
    - *Why:* Django generates migration files with header comments on every `makemigrations`; stripping them by hand is churn that the next generated migration undoes.
    - *Where the reasons went:* `env_ignore_empty=True` makes an empty variable count as unset, because docker-compose passes `DEBUG: ${DEBUG}`, an empty string when the variable is unset, and `DEBUG` stays a real `bool`; list settings use `NoDecode` because the value is a plain comma-separated string, not JSON; emails are matched case-insensitively because rows created before normalisation kept the capitals of their domain (decision 9).

13. **Subagents run on the strongest model (Opus 5.5).**
    - *Why:* a review or research subagent starts with a fresh context and is trusted to find what the main session missed; a weaker model there makes the check cheaper but less useful.
    - *Changed:* `model: opus` in `.claude/agents/reviewer.md`; a rule in `CLAUDE.md` for every other subagent.

14. **The reviewer's Bash hook is a per-command allowlist of flags, and fails closed.**
    - *Why:* the first version denied a list of dangerous flags, which stuck short options (`-Orm`, `-oout.txt`), abbreviated long options (`--open=`, `--untrack`) and options that write (`--log-file`, `--pastebin`) walked past. The reviewer has no Write tool, so the hook is the only barrier against injected text in the repository.
    - *Changed:* every command has the flags it may take, nothing else; `ruff format` is checked on parsed tokens, not the raw string; `docker compose` is limited to `ps` and `config --quiet|--services|--no-interpolate` because plain `config` prints secrets from `.env`; `pytest` needs `--tb=short|line|no` because a long traceback prints the database DSN with its password; `DB_HOST=localhost` is the one allowed environment prefix; an unreadable call or an exception in the hook blocks instead of passing. In `.claude/settings.json` the agent may `git add` and `git commit -m` (it never pushes), so the deny rules carry the protection: the exact spellings of `git add .`, `-A`, `-f`, `git branch -D`, `git switch -C`, `git commit --amend` and `docker compose down|run|exec`, plus mid-pattern forms such as `git add * -f*` for reordered flags. Whether the installed Claude Code honours `*` in the middle of a rule is not verified; if it does not, `git add -v -f .env` is the known gap, and `.env` is also ignored by git. The hook also rejects `{ } ( ) * ? [ ] !` and a leading `~`, because the shell expands them after the hook has approved the text, and pytest `@file` arguments, which load options from a file. If `python3` is missing the hook exits with 127, which Claude Code does not treat as a block; CI runs the hook tests, so a broken script is caught there.
    - *Also:* `tests/test_no_comments.py` scans every Python file outside `migrations/` and only accepts real tool directives; `tests/test_repositories_hold_no_logic.py` rejects `try` and also finds nested or `repositories/` modules.
