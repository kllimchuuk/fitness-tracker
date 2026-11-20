# Specification

Source of truth for architecture. A change to anything in "Fixed decisions" is a decision and goes into
[`DECISIONS.md`](DECISIONS.md), not just into code.

Version: 2026-11-11.

## Goal

A backend that lets a person plan workouts, log what they actually did, and track body weight; and, on top of
that data, an AI coach that proposes and adapts training plans.

The coach has one job: given a user's history and goal, answer "what should I do next, and why". Numbers
(estimated 1RM, next load, volume) come from deterministic code. The language model decides and explains only
where the numbers are not enough.

## Users

A single kind of end user: a person who trains and wants a plan that follows their real results. Staff users
(`is_staff`) maintain the shared exercise catalog.

## Fixed decisions

| Question | Decision |
| --- | --- |
| Web framework | Django only. No second framework or service in this repository |
| API | Django Ninja (typed, OpenAPI) replaces the hand-written `JsonResponse` endpoints |
| Streaming | An async Django view with server-sent events, served under ASGI |
| Training logic | Deterministic engine in plain Python (no ORM inside), unit-tested on its own |
| LLM role | A second opinion called only when the engine is uncertain (cascade); never on the request's critical path without a fallback |
| LLM contract | Strict JSON validated by Pydantic; one retry with the error message; invalid or missing answers are counted, never silently replaced |
| Reproducibility | Every LLM answer is cached by a hash of prompt version, model, provider and input; prompts are versioned files |
| Secrets | Only in `.env` (or the host's secret store); never in the repository or in an image |
| Changes | Small pull requests from `main`, CI must pass |

## Scope

In scope: exercise catalog, workout plans, workout sessions with per-set logs, weight tracking, authentication,
the training engine, the AI coach, a JSON API, an MCP server, background reports.

## What the system deliberately does not do

- It is not medical advice. It does not diagnose, treat injuries or recommend supplements or medication.
- No personal identifiers (email, name) are sent to a language model. The model sees an anonymised training
  description only.
- It does not let the model write to the database unconfirmed: proposed plan changes are validated and
  applied only after the user accepts them.
- No wearable or third-party fitness account integrations.
- No payments, no social features.

## Current state and known gaps

Written honestly so that each item can be closed by a pull request and then removed from this list.

- A workout session stores only its duration, not what was performed (no per-set results).
- `Exercise.type` is a free-text field; there are no muscle groups or equipment.
- `User.status` (ADMIN/CUSTOMER) is a leftover second source of truth next to `is_staff`; `limit_choices_to` and
  the admin still filter by it.
- There is no way to archive an exercise: one used in a plan cannot be deleted, only left in place.
- The repository layer is a thin wrapper, views and services still call `objects.` directly in places (about 20 uses), and the services mix function and class styles.
- `tracker/views.py` mixes HTML views and JSON endpoints in one 600-line module.

## Target architecture

```
Django project
├── authentication/   users, login
├── tracker/          catalog, plans, sessions, weight  (views → service → repository, Pydantic schemas)
├── api/              Django Ninja routers (typed, OpenAPI)
└── agent/
    ├── schemas.py    frozen Pydantic contracts with a schema version
    ├── engine/       deterministic training logic (e1RM, progression, plateau / deload state machine)
    ├── llm/          provider client, rate limiting, response cache, versioned prompts
    ├── cascade.py    when the engine asks the model
    ├── guardrails.py validators every proposed plan must pass
    └── evals/        reproducible evaluation: fixed splits, thresholds chosen on validation only
```

## Invariants

Each one has an acceptance test; a change that touches one keeps its test green. Checklist for reviews: `.claude/skills/invariants-check`.

| ID | Invariant | Acceptance test |
| --- | --- | --- |
| I1 | The engine in `agent/engine/` is plain Python: no ORM, network, clock or randomness | Engine unit tests run with no database; an import check forbids `django` and HTTP clients there |
| I2 | A model call has a timeout and a fallback; without an answer the engine's result stands | A fake client that times out and one that raises both yield the engine's recommendation |
| I3 | The answer is strict JSON validated by Pydantic; one retry carries the error; invalid answers are counted | A fake returning bad JSON twice leaves the counter at 1 failure and no state change |
| I4 | No email, name or user id appears in a prompt, a log line or the cache | A built prompt for a seeded user contains none of the user's identifiers |
| I5 | A plan change is applied only after the guardrails pass and the user accepts it | A proposal never changes `ExerciseSet` until the accept call |
| I6 | System plus own exercises are visible; invisible is 404, visible but not yours is 403 | Existing `test_exercise_permissions.py` plus one case per new route |
| I7 | Authentication is `django.contrib.auth`; JSON answers 401, HTML redirects; logout is POST-only | Existing login tests |
| I8 | The cache key hashes prompt version, model, provider and input | Changing any one of them misses the cache |
| I9 | Secrets only in `.env` | `config/env.py` fails at start-up when a required one is missing |

## Slices

One branch and one pull request per slice, merged with a merge commit.

| Slice | Content | Status |
| --- | --- | --- |
| S0 | CI, hygiene, uv and typed settings, Django auth, exercise ownership, agent configuration (`CLAUDE.md`, `.claude/`) | done |
| S1 | Data model: per-set results, muscle groups and equipment, archived exercises, drop `User.status` | planned |
| S2 | Django Ninja API with OpenAPI, SSE view | planned |
| S3 | Training engine: e1RM, double progression, plateau and deload state machine | planned |
| S4 | LLM client: rate limit, response cache, versioned prompts, fakes | planned |
| S5 | Cascade and guardrails | planned |
| S6 | Evaluation: frozen split, bootstrap confidence intervals, cost report | planned |
| S7 | MCP server, weekly report task, CSV import | planned |
| S8 | README, licence (MIT), final review | planned |

## Quality bar

- CI runs lint, format check and the full test suite on every pull request.
- Tests never touch the network; HTTP, clock and sleep are injected into the LLM client and replaced by fakes.
- The agent ships with an evaluation report that states results and costs, including the unfavourable ones.
