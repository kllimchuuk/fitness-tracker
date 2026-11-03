# Specification

Source of truth for architecture. A change to anything in "Fixed decisions" is a decision and goes into
[`DECISIONS.md`](DECISIONS.md), not just into code.

Version: 2026-10-29.

## Goal

A backend that lets a person plan workouts, log what they actually did, and track body weight; and, on top of
that data, an AI coach that proposes and adapts training plans.

The coach has one job: given a user's history and goal, answer "what should I do next, and why". Numbers
(estimated 1RM, next load, volume) come from deterministic code. The language model decides and explains only
where the numbers are not enough.

## Users

A single kind of end user: a person who trains and wants a plan that follows their real results. An `ADMIN`
status exists for catalog maintenance.

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

- Authentication stores `user_id` in the session by hand instead of using `django.contrib.auth`.
- Any logged-in user can create, edit and delete exercises in the shared catalog.
- `DEBUG` is read as a raw string, so `DEBUG=False` in `.env` still enables debug mode.
- `SECRET_KEY` has no safe failure mode when it is missing.
- The Docker build copies the whole working directory; there was no `.dockerignore` before this change.
- A workout session stores only its duration, not what was performed (no per-set results).
- `Exercise.type` is a free-text field; there are no muscle groups or equipment.
- The repository layer is a thin wrapper and the services mix function and class styles.
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

## Quality bar

- CI runs lint, format check and the full test suite on every pull request.
- Tests never touch the network; HTTP, clock and sleep are injected into the LLM client and replaced by fakes.
- The agent ships with an evaluation report that states results and costs, including the unfavourable ones.
