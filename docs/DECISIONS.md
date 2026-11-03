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
