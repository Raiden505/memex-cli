# MEMORY.md

Living project log for the Recall CLI. Updated by the agent at the end of every working session.
Read this before touching any code. Write to it after every change.

---

## Current State

- **Phase:** 0 — complete
- **Last worked on:** 2026-05-30
- **Last agent action:** Implemented Phase 0 skeleton. All DoD checks pass. Ready to begin Phase 1.

---

## Phase Completion

| Phase | Name                        | Status    | Notes |
|-------|-----------------------------|-----------|-------|
| 0     | Skeleton                    | complete  | DoD verified: banner, /help, /quit, friendly missing-config message |
| 1     | Cloud storage (no AI)       | not started | |
| 2     | Semantic search             | not started | |
| 3     | Answers (RAG complete)      | not started | |
| 4     | Auto intent                 | not started | |
| 5     | Accounts & multi-device     | not started | |
| 6     | Hardening (optional)        | not started | |

---

## Confirmed Values

Fill these in once confirmed against official docs before writing integration code.

- **Gemini chat model ID:** — (`.env.example` uses `gemini-2.5-flash` as a starting point; verify before Phase 3)
- **Gemini embedding model ID:** — (`.env.example` uses `models/text-embedding-004` as a starting point; verify before Phase 2)
- **Embedding output dimension:** — (must equal `vector(N)` in schema; verify before Phase 2)
- **Gemini free-tier RPM/RPD:** —
- **Supabase project URL:** —

---

## Decisions Log

| Date       | Decision | Reason |
|------------|----------|--------|
| 2026-05-30 | `RECALL_USER_ID` env var overrides the default placeholder `user_id` in `Config` | Lets the user set a stable UUID without editing code; the placeholder stays as the default so Phase 1 works out-of-the-box |
| 2026-05-30 | Config validation exits with `sys.exit(1)` via `ConfigError` caught in `main()`, not a top-level exception | Keeps the REPL loop clean; the error is a setup problem, not a runtime fault |
| 2026-05-30 | `pytest` added to `requirements.txt` | Unit tests for router heuristic / config / CLI parsing are required per TDD §12 |

---

## Open Questions / Blockers

- **[BLOCKER for Phase 1]** Need real Supabase project URL and service_role key in `.env` before Phase 1 can be tested.
- **[BLOCKER for Phase 2]** Confirm Gemini embedding model ID and its exact output dimension before Phase 2 work begins. The value in `.env.example` is a best-guess placeholder.
- Confirm Supabase free-tier inactivity-pause behavior before relying on long-idle persistence.

---

## Session Notes

Short log of what each session did. Prepend new entries (newest at top).

### 2026-05-30 — Phase 0
Files created:
- `recall/__init__.py`, `recall/__main__.py`, `recall/cli.py`, `recall/config.py`, `recall/models.py`
- `requirements.txt`, `.env.example`, `README.md`

DoD verified manually:
- `python -m recall` → banner + prompt shown
- `/help` → lists all 8 commands; `/quit` → clean exit
- Missing `.env` vars → prints friendly setup message with list of missing vars, no traceback

### 2026-05-30 — Init
- Initialized repository documentation: created `CLAUDE.md` and `MEMORY.md`.
- No source files existed yet. Project was at pre-Phase-0.
