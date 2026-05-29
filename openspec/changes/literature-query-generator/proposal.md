## Why

Researchers currently translate paper summaries into complex Boolean search queries by hand — a slow, error-prone process involving mismatched brackets, wrong field tags, and invalid wildcard symbols. A dedicated skill that automatically generates syntactically validated search expressions from any Markdown summary (whether produced by `paper-summarizer` or hand-written) eliminates this friction and makes retrieval reproducible.

## What Changes

- Add a new agent skill `.agent/skills/literature-query-generator/` that accepts a Markdown file as input and outputs validated search queries for five academic databases.
- Add a workflow trigger `.agent/workflows/literature-query-generator.md` registering the `/literature-query-generator` slash command.
- Add a supporting Python script `.agent/skills/literature-query-generator/scripts/format_queries.py` implementing per-database query construction and lightweight syntax validation.
- Extend the shared `data/research.db` schema with a new `queries` table (nullable FK to `summaries.id`).
- Ship `.agent/skills/literature-query-generator/assets/example.db` as a self-contained seed database containing the full schema (`papers` + `summaries` + `queries`), so the skill works in fresh-clone environments without depending on another skill's assets.

## Capabilities

### New Capabilities

- `query-generation`: Generate database-specific search query strings from a Markdown summary file. Produces separate, correctly-formatted query strings for Web of Science (`TS=(...)` with double-quote phrases), Scopus (`TITLE-ABS-KEY(...)` with double-quote fuzzy or curly-brace exact phrases), Semantic Scholar, OpenAlex, and CrossRef (flat keyword phrases).
- `query-storage`: Persist generated queries to `data/research.db` in a new `queries` table. Each row links to a `summaries.id` when the MD file originates from `paper-summarizer`; otherwise `summary_id` is NULL and `md_file_path` records the source file path directly.
- `query-deduplication`: Prevent redundant re-generation by checking whether a query already exists for a given MD file + database combination before inserting a new row.

### Modified Capabilities

<!-- No existing spec-level behavior changes. -->

## Impact

- **New files**: `.agent/skills/literature-query-generator/SKILL.md`, `scripts/format_queries.py`, `assets/example.db`; `.agent/workflows/literature-query-generator.md`.
- **Database**: `data/research.db` gains a `queries` table; existing `papers` and `summaries` tables are untouched.
- **Dependencies**: No new Python packages required beyond the standard library (`sqlite3`, `re`, `json`, `hashlib`).
- **Other skills**: `paper-summarizer` is unmodified. The new skill reads from `summaries` via `summary_file_path` lookup but does not write to any existing table.
