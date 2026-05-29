# Design: Simplified Literature Query Generator

## Context

The `paper-summarizer` skill already writes structured Markdown summary cards and logs metadata to `data/research.db` (`papers` + `summaries` tables). To build search queries, we want a simple, direct flow: always call `paper-summarizer` first to ensure we have a valid summary ID, and then generate query strings linked directly to it.

## Goals / Non-Goals

**Goals:**
- Delegate any input file directly to the `paper-summarizer` skill.
- Retrieve the resulting `summary_id` and `summary_content` from the `paper-summarizer` output.
- Generate search query strings for: Web of Science, Scopus, Semantic Scholar, OpenAlex, CrossRef.
- Persist queries to `data/research.db` in a new `queries` table with a non-null foreign key `summary_id` referencing `summaries(id)`.
- Deduplicate based strictly on the `(summary_id, database)` pair.

**Non-Goals:**
- Supporting inputs without a summary (no standalone/handwritten files are processed without first passing through `paper-summarizer`).
- Modifying existing `papers` or `summaries` tables.

## Decisions

### Decision 1: Delegation-first routing
**Choice:** Always call `paper-summarizer` first.
**Rationale:** This guarantees we have a database record under `summaries` for every processed document, meaning `summary_id` is always non-null. This removes the need for path normalization, standalone file routing, and nullable foreign keys in the `queries` table.

### Decision 2: Streamlined Schema
**Choice:**
```sql
CREATE TABLE IF NOT EXISTS queries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id   INTEGER NOT NULL,
    database     TEXT NOT NULL,
    query_string TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (summary_id) REFERENCES summaries (id) ON DELETE CASCADE
)
```
**Rationale:** Eliminates `md_file_path` column entirely since queries are strictly associated with a summary (and through it, a paper).

### Decision 3: Simple Deduplication
**Choice:** Uniqueness key is `(summary_id, database)`.
**Rationale:** Simplifies lookup query to `SELECT 1 FROM queries WHERE summary_id = ? AND database = ? LIMIT 1`.

### Decision 4: Database Check and Replacement Precondition
**Choice:** Before initiating execution or calling the `paper-summarizer` skill, check if `data/research.db` exists and contains the `queries` table. If the database file does not exist, or if it exists but does NOT contain the `queries` table, delete the database file (if present), copy the existing `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and programmatically create the `queries` table inside it using a SQL statement.
**Rationale:** Reuses the existing `example.db` template from the `paper-summarizer` skill instead of duplicating binary assets inside the new skill's directory, ensuring a clean and consistent database state.

### Decision 5: Database Query Cache Check Short-Circuiting
**Choice:** If all five database queries (Web of Science, Scopus, Semantic Scholar, OpenAlex, CrossRef) already exist in the database for the resolved `summary_id` (and `--force` is NOT specified), the workflow short-circuits: it skips LLM keyword synthesis and formatter script execution entirely, reading the query strings directly from SQLite and rendering them.
**Rationale:** Saves token costs and significantly speeds up execution on repeat runs of the same document by bypassing the LLM call when all queries are already cached.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| `paper-summarizer` fails or aborts (e.g. non-academic doc) | The query builder catches this and aborts immediately without storing any queries or generating output. |
