# MEMORY.md

Living project log for the Recall CLI. Updated by the agent at the end of every working session.
Read this before touching any code. Write to it after every change.

---

## Current State

- **Phase:** 4 — code complete, ready for live DoD test
- **Last worked on:** 2026-05-30
- **Last agent action:** Reverted Phase 5 back to Phase 4 at user request. auth.py deleted, schema.sql back to RLS off, cli.py login step removed, .env.example back to service_role key.

---

## Phase Completion

| Phase | Name                        | Status    | Notes |
|-------|-----------------------------|-----------|-------|
| 0     | Skeleton                    | complete  | DoD verified: banner, /help, /quit, friendly missing-config message |
| 1     | Cloud storage (no AI)       | code complete — needs live Supabase DoD test | run schema.sql in Supabase dashboard first |
| 2     | Semantic search             | code complete — needs live DoD test | /add now embeds; /search queries by meaning |
| 3     | Answers (RAG complete)      | code complete — needs live DoD test | /ask: embed → search → synthesize; no-hallucination short-circuit in place |
| 4     | Auto intent                 | code complete — needs live DoD test | heuristic + LLM classifier; bare text routes to store or query automatically |
| 5     | Accounts & multi-device     | not started | reverted at user request |
| 6     | Hardening (optional)        | not started | |

---

## Confirmed Values

Fill these in once confirmed against official docs before writing integration code.

- **Chat model ID:** `gemma-4-26b-a4b-it` (user preference — Gemma 4 26B MoE, available via Gemini API on AI Studio)
- **Gemini embedding model ID:** `gemini-embedding-001` (confirmed — `text-embedding-004` shut down Jan 2026)
- **Embedding output dimension:** 768 (confirmed — model default is 3072, truncated to 768 via `output_dimensionality` param, no quality loss per MRL)
- **Gemini free-tier RPM/RPD:** — (check https://ai.google.dev/gemini-api/docs/rate-limits before Phase 6)
- **Supabase project URL:** — (user-specific)

---

## Decisions Log

| Date       | Decision | Reason |
|------------|----------|--------|
| 2026-05-30 | `RECALL_USER_ID` env var overrides the default placeholder `user_id` in `Config` | Lets the user set a stable UUID without editing code; the placeholder stays as the default so Phase 1 works out-of-the-box |
| 2026-05-30 | Config validation exits with `sys.exit(1)` via `ConfigError` caught in `main()`, not a top-level exception | Keeps the REPL loop clean; the error is a setup problem, not a runtime fault |
| 2026-05-30 | `pytest` added to `requirements.txt` | Unit tests for router heuristic / config / CLI parsing are required per TDD §12 |
| 2026-05-30 | `ALTER TABLE memories DISABLE ROW LEVEL SECURITY` added explicitly to schema.sql | Supabase enables RLS by default on all new tables; without this the service_role key still gets blocked on insert |
| 2026-05-30 | `task_type="RETRIEVAL_DOCUMENT"` on store, `task_type="RETRIEVAL_QUERY"` on search | Without task types, all memories score ~0.59 regardless of relevance — the model compresses scores into a narrow band. Task types restore meaningful ranking separation. |
| 2026-05-30 | Chat model changed from `gemini-2.5-flash` to `gemma-4-26b-a4b-it` | User preference. Model is a 26B MoE (4B active params) available via Gemini API. No code changes — model ID is read from `CHAT_MODEL` env var. |
| 2026-05-30 | Session saved to `~/.recall/session.json` (not inside the project dir) | Keeps credentials out of the repo entirely; works cross-platform via `Path.home()` |
| 2026-05-30 | `cfg.user_id` mutated after login in `main()` | Cleanest way to thread the authenticated UUID through all existing store calls without changing any function signatures |

---

## Open Questions / Blockers

- **[ACTION for Phase 1 DoD]** Fill in real `SUPABASE_URL` and `SUPABASE_KEY` (service_role) in `.env`, then run `supabase/schema.sql` in the Supabase SQL editor. After that, test: `/add buy milk` → id appears; `/list` shows it; `/count` correct; `/forget <id>` removes it; quit+relaunch persists.
- **[ACTION for Phase 2 DoD]** Add `GEMINI_API_KEY` and set `EMBED_MODEL=gemini-embedding-001` in `.env`. Add a few distinct memories with `/add`, then test `/search` with different wording — right notes should surface with sensible similarity scores.
- Confirm Supabase free-tier inactivity-pause behavior before relying on long-idle persistence.

---

## Session Notes

Short log of what each session did. Prepend new entries (newest at top).

### 2026-05-30 — Phase 5 (reverted)
Phase 5 was implemented then reverted at user request. All changes undone:
- `recall/auth.py` deleted
- `supabase/schema.sql` back to `DISABLE ROW LEVEL SECURITY`
- `recall/cli.py` login step removed
- `.env.example` back to service_role key + RECALL_USER_ID option restored

### 2026-05-30 — Phase 4
Files created/modified:
- `recall/router.py` — new; `route(text, cfg)`: heuristic handles ends-with-?, query-starter words, "did/do/have i" prefixes; ambiguous input falls through to `classify_intent`
- `recall/llm.py` — added `classify_intent(text, cfg)`: calls chat model at temp 0 with a few-shot STORE/QUERY system prompt; defaults to "store" on any exception
- `recall/cli.py` — bare text now routes through `router.route`; extracted `_do_store` and `_do_query` helpers shared by slash commands and auto-routing; removed `_NOT_YET` stub

DoD: test "remind me to call mom" (→ STORE) and "remind me where I parked" (→ QUERY). All slash commands still work.

### 2026-05-30 — Phase 3
Files created/modified:
- `recall/llm.py` — new; `synthesize_answer(question, memories, cfg)` calls `gemini-2.5-flash` at temperature 0.2 with a strict no-hallucination system prompt; short-circuits to a fixed message if no memories are passed (no LLM call)
- `recall/cli.py` — `/ask` wired: embed (RETRIEVAL_QUERY) → search_memories → synthesize_answer → print

Confirmed: `gemini-2.5-flash` is on free tier (10 RPM, ~250 RPD).
DoD status: code complete, imports verified. Test with `/ask` on stored content and on unstored content.

### 2026-05-30 — Phase 2
Files created/modified:
- `recall/embeddings.py` — new; `embed(text, cfg)` calls `gemini-embedding-001` with `output_dimensionality=768`
- `recall/cli.py` — `/add` now embeds before storing; `/search` wired (embed → search_memories → ranked results with similarity scores); `/ask` still a stub
- `.env.example` — updated `EMBED_MODEL` from dead `text-embedding-004` to `gemini-embedding-001`

Key finding: `text-embedding-004` was shut down Jan 14 2026. Use `gemini-embedding-001` (free tier, 768-dim output via MRL truncation).
DoD status: code complete, imports verified. Needs live Gemini API key to test.

### 2026-05-30 — Phase 1
Files created/modified:
- `supabase/schema.sql` — table, HNSW index, `match_memories` RPC (RLS off)
- `recall/store.py` — `get_client`, `add_memory`, `list_memories`, `delete_memory`, `count_memories`, `search_memories` (search_memories is a Phase 2 stub, included to complete the contract)
- `recall/cli.py` — wired `/add`, `/list`, `/count`, `/forget`; banner now shows live count from DB; `/ask` and `/search` still print not-yet stub

DoD status: code complete, imports verified. Needs real Supabase credentials + schema applied to run the live acceptance tests.

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
