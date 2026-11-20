---
name: spec-slice
description: Work loop for implementing one slice (S0-S8) of the Fitness Tracker spec. Use when starting or continuing a slice, adding a feature package, or when the user says "next slice" or names one. Covers reading the spec, branching, test first, implementation rules, checks and the local commit.
---

# Implementing a slice

Follow these steps in order. The slice list is in `docs/SPEC.md` (Slices); the rules behind it are in `CLAUDE.md`.

1. **Read.** Open the slice in the SPEC and every section it names (Fixed decisions, Invariants, Target architecture, Acceptance tests). If the SPEC is silent or wrong, stop and report "Decision needed" with a recommendation; do not guess.
2. **Branch.** Check `git branch --show-current`. Work on a branch named by commit type for this slice (`feat/exercise-set-logs`). Never on `main`. If it does not exist, create it with `git switch -c`.
3. **Test first.** Write the failing test for the acceptance criterion in `tests/`, against real PostgreSQL with factories from `tests/factories`. Run it and see it fail for the right reason.
4. **Implement.** Smallest code that passes, following `CLAUDE.md`:
   - views and API routes -> service -> repository; routes hold no logic;
   - all queries in repositories, repositories hold no logic and take plain arguments;
   - the engine in `agent/engine/` imports no Django and no network client;
   - a migration for every model change, one per slice;
   - no comments in Python code.
5. **Check.** `uv run ruff check .`, `uv run ruff format --check .`, `DB_HOST=localhost uv run pytest --no-cov -q`, `uv run python manage.py makemigrations --check --dry-run`. Everything green before handing over.
6. **Document.** If the change deviates from the SPEC or settles a choice, add the entry to `docs/DECISIONS.md` and edit the SPEC in the same change.
7. **Commit locally.** Stage by explicit path, never `git add .`, never `.env`. One logical change per commit, module and its tests together. Conventional Commits subject in English describing the behavior, no attribution trailer. Never push, never amend or reset history.
8. **Report** in the `report` skill's shape, with `git log --stat main..HEAD`. Suggest running the `reviewer` subagent before the pull request is opened.

If a step fails twice for the same reason, stop and say what you tried instead of looping.
