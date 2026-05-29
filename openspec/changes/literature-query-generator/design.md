## Context

The `paper-summarizer` skill already writes structured Markdown summary cards to `data/papers/summaries/` and logs metadata to `data/research.db` (`papers` + `summaries` tables). Researchers must then manually craft Boolean search strings for each target database — a tedious, error-prone step that produces non-reproducible queries.

The `literature-query-generator` skill plugs into this workflow by acting as a universal query builder. It accepts Markdown (.md), PDF (.pdf), or DOCX (.docx) files. For Markdown inputs, it checks the database to see if it is an existing summary and links queries accordingly. For raw PDF or DOCX files, it delegates summary generation to `paper-summarizer` first, then generates and links queries to the newly created summary database record.

Current constraints:
- `data/research.db` schema must not change for existing tables (`papers`, `summaries`).
- The skill must be self-contained; it cannot depend on `paper-summarizer`'s `assets/example.db`.
- Standard library only (no third-party packages).

## Goals / Non-Goals

**Goals:**
- Accept Markdown (.md), PDF (.pdf), and DOCX (.docx) files as input, routing them based on file format.
- Integrate with the `paper-summarizer` skill to process raw PDF/DOCX documents first before constructing queries.
- Query database `summaries` table to lookup matching entries for input Markdown paths to maintain referential integrity.
- Produce per-database query strings for: Web of Science, Scopus, Semantic Scholar, OpenAlex, CrossRef.
- Validate query syntax (balanced parentheses/brackets, no illegal characters per database).
- Persist queries to `data/research.db` in a new `queries` table with a nullable FK to `summaries.id`.
- Deduplicate: do not re-insert a query if the same MD file (or its summary ID) + database combination already has a row.
- Ship a self-contained `assets/example.db` containing the full three-table schema for fresh-clone scenarios.

**Non-Goals:**
- Executing queries against live databases (no HTTP requests).
- Modifying `papers` or `summaries` tables (except transitively when delegating to `paper-summarizer` which registers them).
- Producing relevance-ranked results.
- Supporting databases beyond the five listed above in this version.

## Decisions

### Decision 1: Two distinct query formats (WoS vs. Scopus)

**Choice:** Generate `TS=(...)` with double-quoted phrases for WoS; generate `TITLE-ABS-KEY(...)` with double-quoted fuzzy phrases (and optionally curly-brace exact phrases) for Scopus.

**Rationale:** `TS=` is WoS-specific and does not exist in Scopus. Scopus uses `TITLE-ABS-KEY(field)` syntax. Treating them as the same "single-tag" format would produce invalid queries. Double quotes in Scopus allow plural/variant matching; curly braces enforce exact match but disallow wildcards — the skill will use double quotes by default.

**Alternative considered:** A single template with a substitutable field-tag placeholder — rejected because the surrounding syntax (parentheses placement, boolean capitalization) also differs between the two systems.

---

### Decision 2: `queries.summary_id` nullable FK

**Choice:** `summary_id INTEGER` with `FOREIGN KEY (summary_id) REFERENCES summaries(id) ON DELETE SET NULL`.

**Rationale:** Queries can be generated from hand-written MD files that have no entry in `summaries`. Forcing a non-null FK would require inserting dummy rows into `summaries`, polluting that table. Nullable FK keeps the two tables independent while preserving the link when it exists.

**Alternative considered:** A separate `standalone_queries` table for non-summary inputs — rejected as unnecessary complexity; a single `queries` table with a conditional NULL FK is simpler to query.

---

### Decision 3: Keyword extraction strategy

**Choice:** LLM-based semantic keyword synthesis/extraction from the entire Markdown content, passed via command-line arguments to the script, with local regex heuristics maintained as a fallback.

**Rationale:** Regex-based heuristic keyword extraction is blind to semantic context and can produce poor-quality, noisy query terms from free-form or non-standard Markdown files. By using the LLM to read the entire document, understand its core scientific contributions, and synthesize the most appropriate search terms, we generate queries of much higher relevance. We pass these terms to the Python script to leverage its deterministic formatting, validation, and database operations.

**Alternative considered:** Generating raw SQL or formatted queries entirely via LLM without a supporting script — rejected because deterministic validation (parentheses balancing, query escaping, exact/fuzzy rules) and database integrity checks (deduplication, relative path resolution) are safer and more robust when handled by code.

---

### Decision 4: `assets/example.db` as full three-table seed

**Choice:** The `literature-query-generator` skill ships its own `example.db` containing `papers`, `summaries`, and `queries` tables (schema identical to `paper-summarizer`'s tables plus the new `queries` table).

**Rationale:** If `data/research.db` does not exist (fresh clone), the skill needs a seed to copy. If it only contained the `queries` table, subsequent FK lookups against `summaries` would fail. Replicating the three-table schema makes the skill fully standalone.

**Alternative considered:** Reading `paper-summarizer/assets/example.db` and adding the `queries` table at runtime — rejected because it creates a cross-skill asset dependency, violating the isolation principle.

---

### Decision 5: Script decomposition

The skill scripts are split into three focused modules:
- `format_queries.py` — keyword extraction + per-database query construction + validation.
- `db_logger.py` — DB init (CREATE TABLE IF NOT EXISTS for `queries`), lookup helpers, `store_query`, `get_queries_for_md`.
- `__init__.py` — empty package marker.

This mirrors the modular pattern established by `paper-summarizer`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| LLM extracts irrelevant or sub-optimal keywords from complex MD files | Skill prompt rules instruct the LLM to read the entire MD file, understand the scientific concepts, and synthesize precise, relevant keyword terms. The user/agent can also review and manually override if needed. |
| `summaries` table lookup by `summary_file_path` may fail due to slash formatting differences or match stale summary runs when a paper is re-summarized | Normalize all path candidates to check both forward and backward slashes, and resolve to the latest (highest ID) `summaries.id` row |
| Duplicate detection relies on `(md_file_path, database)` uniqueness — re-running on unchanged file always skips | Add a `--force` flag to `format_queries.py` to allow deliberate re-generation |
| `example.db` schema diverges from `paper-summarizer` over time | Both skills define tables with `CREATE TABLE IF NOT EXISTS`; divergence only matters if column definitions conflict — document this constraint |

## Migration Plan

1. Run `python .agent/skills/literature-query-generator/scripts/db_logger.py init` — adds `queries` table to existing `data/research.db` without touching other tables.
2. No rollback required: dropping the `queries` table restores the prior state.
3. On fresh clone: `db_logger.py init` copies `assets/example.db` to `data/research.db` if missing, then creates `queries` via `CREATE TABLE IF NOT EXISTS`.

## Open Questions

- Should the skill also output a human-readable Markdown block (in addition to JSON) for direct paste into the IDE chat? This would be useful for quick inspection without querying the DB.
- Should `--force` re-insert with a new timestamp, or update the existing row in place?
