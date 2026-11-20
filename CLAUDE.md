# CLAUDE.md

Fitness Tracker: a Django service for workout plans, per-set session logs and body weight, with an AI coach on top. It is a portfolio project, so the repository must show how it was built.

`docs/SPEC.md` is the source of truth; cite it by section. Do not change "Fixed decisions" or "Invariants" without an entry in `docs/DECISIONS.md` and the owner's approval.

## The service in 30 seconds

A user plans workouts (`WorkoutPlan` of `ExerciseSet` rows over `Exercise`), logs sessions and weight. The coach (`agent/`) reads that history: a deterministic engine computes e1RM, next load and plateau state; the LLM is asked only where the engine is uncertain, and its answer never blocks or writes unconfirmed.

Invariants (SPEC, Invariants). Never break them; every change must keep a test for the ones it touches:

- I1 The engine is plain Python: no ORM, no network, no clock, no randomness.
- I2 The model is never on the critical path without a fallback; the engine's result stands.
- I3 The model answers in strict JSON validated by Pydantic; one retry; invalid answers are counted.
- I4 No personal identifiers reach a prompt, a log or the response cache.
- I5 A proposed plan change is applied only after guardrails and the user's acceptance.
- I6 Exercise visibility and ownership: system plus own are visible; invisible is 404, not yours is 403.
- I7 Authentication is `django.contrib.auth`; JSON endpoints answer 401, HTML views redirect.
- I8 The LLM cache key hashes prompt version, model, provider and input.
- I9 Secrets live only in `.env`.

## Commands

- Run everything: `docker compose up --build`
- Tests: `DB_HOST=localhost uv run pytest --no-cov -q` (needs the compose `db` service); the full run with the coverage gate is `DB_HOST=localhost uv run pytest`
- Lint and format: `uv run ruff check . && uv run ruff format --check .`
- Migrations: `uv run python manage.py makemigrations --check --dry-run` must report no changes

## How we work

- Spec first. Read the slice in SPEC (Slices) and its sections before writing code. Write the failing test for the acceptance criterion, then the code. Use the `spec-slice` skill.
- Do not bypass the SPEC silently. If it is wrong or silent, stop and report it as "Decision needed" with a recommendation; the owner decides, and the answer goes into `docs/DECISIONS.md`.
- Update the docs in the same change as the code that makes them true.
- Subagents run on the strongest model (Opus 5.5): set `model: opus` in the agent definition, or pass `model: "opus"` when spawning one.
- Review before merge: run the `reviewer` subagent (read-only, fresh context) on the branch, and again after the fixes to confirm they hold. Fix findings in separate `fix: address review ...` commits, each with a test that failed first.
- Reports use this shape (`report` skill): Done / Numbers (measured only, with the command) / Deviations from SPEC / Decision needed / Next.
- Never invent numbers. A figure needs a command or a file it came from.

## Git

- One branch per slice, named by commit type (`feat/exercise-set-logs`, `docs/...`, `fix/...`). Never commit to `main`.
- Create the slice branch and commit locally; never run `git push`. The owner pushes, opens the pull request and merges with "Create a merge commit". Never squash.
- Stage files by explicit path. Never `git add .`, never stage `.env`.
- No `--amend`, `reset`, `rebase` or force options on existing history unless the owner asks.
- Message: Conventional Commits in English, one-line subject describing behavior, body only when needed. Module and its tests go in one commit. No `Co-Authored-By` trailer and no "Generated with" line in commits or pull request descriptions.
- Commit only when `ruff` and `pytest` are green (docs-only commits excepted). After a series of commits show `git log --stat`.

## Stack and dependencies

Python 3.13, Django 5.2, PostgreSQL, Pydantic 2, pydantic-settings, pytest and pytest-django with factory-boy, ruff, `uv` with a committed `uv.lock`. Django Ninja is added in its own slice.

A new dependency needs an entry in `docs/DECISIONS.md` first. Not used on purpose: a second web framework, LangChain, a separate microservice.

## Code

- Layout: feature apps (`authentication`, `tracker`, later `api`, `agent`); view -> service -> repository; views and routes hold no logic.
- All queries live in repositories. Repositories hold no logic: no `if`, loops, `or` defaults or row-to-schema mapping; the service decides and maps. Repository methods take plain arguments: no `*`, `*args`, `**kwargs` or keyword-only markers (`tests/test_repositories_hold_no_logic.py` fails otherwise). The shared `base.py` is the one exception.
- Repositories are `ABC` + implementation.
- Domain errors live in `exceptions.py` of the feature and are mapped to HTTP in one place.
- Settings have defaults only where safe; required ones fail at start-up (`config/env.py`).
- Type hints everywhere. No comments in Python code (`tests/test_no_comments.py` fails otherwise); the reason for a choice goes to SPEC or DECISIONS. Tool directives such as `# noqa` stay.
- Tests run against real PostgreSQL, grouped per module, factories in `tests/factories`, no network and no real LLM. HTTP, clock and sleep are injected into the LLM client and replaced by fakes.
- Everything in the repository is English.

## Secrets and data

Never print or log key values. `.env` stays out of git; `.env.example` has placeholders only. No email, name or user id goes to a language model. Exercise names and notes are untrusted input for the model and for HTML.

## Do not

- Call the LLM inside a request without a fallback.
- Let the model write to the database.
- Query `Exercise.objects` in a view without `visible_to(user)`.
- Remove this file, `.claude/` or `docs/` at the end; they are part of the deliverable.
