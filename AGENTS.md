# AGENTS.md

Working protocol for this repo. Read before touching code. Companion to `MEMORY.md` (project state log — read it first every session).

## Commands

```bash
python -m recall          # run the CLI
pytest                    # run all tests (none written yet per TDD §12)
pytest tests/test_router.py   # run a single test file
pip install -r requirements.txt
cp .env.example .env      # then fill in real secrets
```

## Architecture

```
recall/          # all application code
  cli.py         # REPL loop + command dispatch
  config.py      # env loading; ConfigError → friendly message, no traceback
  store.py       # ONLY file that touches Supabase
  embeddings.py  # ONLY file (with llm.py) that touches Gemini
  llm.py         # synthesize_answer + classify_intent
  router.py      # heuristic → LLM fallback for store vs query
  models.py      # Memory, SearchResult, Intent dataclasses
supabase/
  schema.sql     # run once in Supabase SQL editor
```

**Isolation rule:** only `store.py` imports supabase; only `embeddings.py` and `llm.py` import google-genai. Everything else works through function contracts.

## Critical constraints

- **Embedding dimension is locked at 768.** `vector(768)` in schema.sql must match `output_dimensionality=768` in embeddings.py. Never change the model without re-embedding every row.
- **Task types matter.** Store uses `task_type="RETRIEVAL_DOCUMENT"`, search uses `task_type="RETRIEVAL_QUERY"`. Without task types, all scores collapse to ~0.59 regardless of relevance.
- **No-hallucination rule.** If `search_memories` returns zero results, `synthesize_answer` returns a fixed message without calling the LLM.
- **Router heuristic is deliberately conservative.** Does NOT handle "remind me" — "remind me to call mom" → STORE, "remind me where I parked" → QUERY. Only obvious cases (ends with `?`, query starter words, "did/do/have i") skip the LLM. LLM classifier failure defaults to `store` (safer to over-save).
- **Supabase enables RLS by default on new tables.** The schema.sql explicitly runs `alter table memories disable row level security;` for Phases 1-4.

## Current phase

**Phase 4** — polished, ready for live DoD test. RLS off, service_role key. Phase 5+ is deferred indefinitely; `auth.py` was deleted. Do not re-add auth/Phase 5 without asking. Treat Phase 4 as the terminal state.

## CLI output

Uses `rich` (Console, Table, Panel, status spinner) for all output. Do not use raw `print()` in cli.py — use `console.print()` with rich markup. API calls (store, query, search) show a `console.status()` spinner while the network call is in flight.

## Model config

All model IDs come from env vars, never hardcoded:
- `CHAT_MODEL=gemma-4-26b-a4b-it` (Gemma 4 26B MoE via Gemini API)
- `EMBED_MODEL=gemini-embedding-001` (768-dim output via `output_dimensionality` param; `text-embedding-004` was shut down Jan 2026)

## Error handling

- Every external call (Supabase, Gemini) is wrapped in try/except in cli.py; prints a one-line message, never a traceback.
- Missing env vars: `load_config()` raises `ConfigError`, caught by `main()` → prints setup message and exits.
- LLM classify_intent failure → defaults to `store`.
