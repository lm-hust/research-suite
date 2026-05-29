## Context

The `paper-summarizer` skill already writes structured Markdown summary cards to `data/papers/summaries/` and logs metadata to `data/research.db` (`papers` + `summaries` tables). Researchers must then manually craft Boolean search strings for each target database — a tedious, error-prone step that produces non-reproducible queries.

The `literature-query-generator` skill plugs into this workflow as a downstream step: it reads an MD file (structured or ad-hoc), extracts key search concepts, generates correctly-formatted query strings for each target database, and persists the results.

Current constraints:
- `data/research.db` schema must not change for existing tables (`papers`, `summaries`).
- The skill must be self-contained; it cannot depend on `paper-summarizer`'s `assets/example.db`.
- Standard library only (no third-party packages).

## Goals / Non-Goals

**Goals:**
- Accept any Markdown file as input (structured summary card or hand-written notes).
- Produce per-database query strings for: Web of Science, Scopus, Semantic Scholar, OpenAlex, CrossRef.
- Validate query syntax (balanced parentheses/brackets, no illegal characters per database).
- Persist queries to `data/research.db` in a new `queries` table with a nullable FK to `summaries.id`.
- Deduplicate: do not re-insert a query if the same MD file + database combination already has a row.
- Ship a self-contained `assets/example.db` containing the full three-table schema for fresh-clone scenarios.

**Non-Goals:**
- Executing queries against live databases (no HTTP requests).
- Modifying `papers` or `summaries` tables.
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

**Choice:** Heuristic extraction from MD content — scan for `**Keywords**` / `## Keywords` sections first; fall back to noun-phrase extraction from headings and bold text.

**Rationale:** `paper-summarizer` cards have a predictable `## Keywords` section. Hand-written MDs do not; a graceful fallback prevents hard failures. No NLP libraries are available (standard library constraint), so the fallback uses regex-based heading and bold-text scanning.

**Alternative considered:** Requiring a structured YAML front-matter block in all input MDs — rejected as it imposes a format on users writing ad-hoc notes.

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
| Keyword extraction produces low-quality terms from free-form MDs | Skill prompt rules instruct the LLM to review extracted keywords before finalizing; output is human-readable before DB insert |
| `summaries` table lookup by `summary_file_path` may fail if paths change | Store relative paths in `summaries`; lookup uses `os.path.abspath` normalization |
| Duplicate detection relies on `(md_file_path, database)` uniqueness — re-running on unchanged file always skips | Add a `--force` flag to `format_queries.py` to allow deliberate re-generation |
| `example.db` schema diverges from `paper-summarizer` over time | Both skills define tables with `CREATE TABLE IF NOT EXISTS`; divergence only matters if column definitions conflict — document this constraint |

## Migration Plan

1. Run `python .agent/skills/literature-query-generator/scripts/db_logger.py init` — adds `queries` table to existing `data/research.db` without touching other tables.
2. No rollback required: dropping the `queries` table restores the prior state.
3. On fresh clone: `db_logger.py init` copies `assets/example.db` to `data/research.db` if missing, then creates `queries` via `CREATE TABLE IF NOT EXISTS`.

## Open Questions

- Should the skill also output a human-readable Markdown block (in addition to JSON) for direct paste into the IDE chat? This would be useful for quick inspection without querying the DB.
- Should `--force` re-insert with a new timestamp, or update the existing row in place?
