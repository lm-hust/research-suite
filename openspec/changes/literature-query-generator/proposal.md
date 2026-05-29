# Proposal: Simplified Literature Query Generator

## Why

Researchers need to build Boolean search queries for multiple academic databases based on literature summaries. The previous design was over-complicated, handling complex path routing, standalone markdown lookups, and nullable database fields. By refactoring the process to **always** run the `paper-summarizer` skill first (which parses the input and logs a valid summary row), we simplify query generation into a single deterministic flow: generating search queries linked to a guaranteed, non-null `summary_id`.

## What Changes

- **Simplified Routing**: The `/literature-query-generator` command accepts any input file (`.pdf`, `.docx`, `.md`, `.txt`) and immediately delegates it to the `paper-summarizer` skill.
- **Database Initialization Precondition**: Before calling `paper-summarizer`, the workflow checks if `data/research.db` contains the `queries` table. If the database is missing or does not contain `queries`, it deletes the database file (if present), copies the existing `example.db` from the `paper-summarizer` skill's assets, and programmatically creates the `queries` table inside it.
- **Unified Query Generation**: The workflow retrieves the `summary_id` and `summary_content` returned by `paper-summarizer`, uses LLM semantic keyword synthesis on the summary content, and runs a streamlined Python script to format and persist the queries.
- **Streamlined Database Schema**: The `queries` table is simplified to use a non-null foreign key `summary_id` referencing `summaries(id)`. We remove the `md_file_path` column entirely.
- **Workflow Command**: The workflow trigger `.agent/workflows/literature-query-generator.md` is updated to implement this direct calling chain.

## Capabilities

### New Capabilities

- `query-generation`: Generate correctly formatted query strings for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from the summary card content.
- `query-storage`: Persist queries in a simplified table linked directly to a non-null `summary_id`.

### Modified Capabilities

- None (deletes the old, complex routing and standalone Markdown handling capabilities).

## Impact

- **Database**: The `queries` schema is simplified (no `md_file_path` column, non-null `summary_id` foreign key).
- **Code Cleanliness**: The CLI script and helper functions in `format_queries.py` and `db_logger.py` are stripped of path normalization and standalone file lookup logic.
