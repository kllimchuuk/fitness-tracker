---
name: invariants-check
description: Checklist of the Fitness Tracker invariants (SPEC, Invariants) with concrete things to look for in code and tests. Use when reviewing a diff, before committing changes to permissions, authentication, the training engine, the LLM client or the cascade, or when asked whether a change is safe.
---

# Invariant checklist

For each item answer pass, fail or not touched, and point at the code or test that proves it. The source is `docs/SPEC.md` (Invariants).

| ID | Look for | Red flag |
|---|---|---|
| I1 | `agent/engine/` is plain Python: inputs and outputs are frozen Pydantic or dataclass values. | An import of `django`, `tracker.models`, an HTTP client, `time` or `random` inside the engine. |
| I2 | Every call to the model sits behind the cascade with a timeout and the engine's result as the fallback. | A view or task that awaits the model with no fallback; an exception from the client reaching the user. |
| I3 | The model's answer is parsed into a Pydantic model; one retry carries the validation error; invalid or missing answers are counted. | `json.loads` on the answer without validation; a silent default that hides a failed answer. |
| I4 | A prompt is built from an anonymised training description. | An email, name, user id or free-text note in a prompt, a log line or the response cache. |
| I5 | A proposed plan change is stored as a proposal and applied only by an explicit user action, after the guardrails. | The model's output written to `WorkoutPlan` or `ExerciseSet` directly. |
| I6 | Exercises are read through `Exercise.objects.visible_to(user)`; invisible is 404, visible but not changeable is 403; staff create system exercises, users create private ones. | `Exercise.objects.get(pk=...)` in a view; an ownership check done only in the template; a plan accepting an exercise the user cannot see. |
| I7 | Login state comes from `request.user`; HTML views redirect, JSON endpoints answer 401; logout is POST-only; `?next=` is same-host only. | A `session["user_id"]` read; a state-changing GET; an open redirect. |
| I8 | The cache key hashes prompt version, model, provider and input; prompts are versioned files. | A prompt edited in place without a version bump; a key missing the model name. |
| I9 | Secrets come from `config/env.py` and `.env`; `.env.example` has placeholders only. | A key in code, in a test, in an image layer or in a log line. |

Structure and safety checks that apply to every diff:

- Queries outside a repository, or a view or route containing logic; a repository containing `if`, loops, `or` defaults or row mapping.
- A model change without a migration, or a migration that edits old data without a reverse step.
- A new `ModelSerializer`-style or `JsonResponse` endpoint where a Ninja route is expected once the API slice has landed.
- Secrets, API keys, provider response bodies or full user notes in log lines or error responses.
- Untrusted text (exercise name, notes, model answer) rendered with `|safe`, `mark_safe` or `innerHTML`.
- A new dependency without a `docs/DECISIONS.md` entry.
- Behavior change without a test, or a test that cannot fail. For every new test name the bug that would make it fail; a test that passes on a stub or on an empty implementation proves nothing.
- A test that touches the network, the real clock or a real LLM.
- A docs file that no longer matches the code (SPEC, DECISIONS, README, `.env.example`).
