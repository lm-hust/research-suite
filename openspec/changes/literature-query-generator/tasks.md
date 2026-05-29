## 1. Scaffold Skill Directory Structure

- [x] 1.1 Create `.agent/skills/literature-query-generator/` directory with `__init__.py`, `SKILL.md` placeholder, `scripts/` and `assets/` subdirectories
- [x] 1.2 Create `.agent/workflows/literature-query-generator.md` workflow file to register the `/literature-query-generator` slash command
- [x] 1.3 Add `.gitkeep` to `assets/` to ensure the directory is tracked by Git before the example DB is generated

## 2. Build `assets/example.db` Seed Database

- [x] 2.1 Write a one-off setup script `scripts/create_example_db.py` that creates a fresh SQLite DB with the full three-table schema (`papers`, `summaries`, `queries`)
- [x] 2.2 Run the script to generate `assets/example.db`; verify all three tables exist with correct columns and FK constraints
- [x] 2.3 Delete `scripts/create_example_db.py` after the DB is generated (temporary file cleanup)
- [x] 2.4 Add `assets/example.db` to Git tracking (ensure `.gitignore` does not exclude it)

## 3. Implement `scripts/db_logger.py`

- [x] 3.1 Implement `init_db()`: copy `assets/example.db` → `data/research.db` if DB is missing; then apply `CREATE TABLE IF NOT EXISTS` for `queries` table only (never ALTER/DROP existing tables)
- [x] 3.2 Implement `resolve_summary_id(md_file_path)`: connect to DB, query `summaries` table by `summary_file_path`, return `summary_id` or `None`
- [x] 3.3 Implement `check_duplicate(summary_id, md_file_path, database)`: return `True` if a matching row already exists in `queries` (using nullable FK logic described in spec)
- [x] 3.4 Implement `store_query(summary_id, md_file_path, database, query_string)`: insert a new row into `queries`
- [x] 3.5 Implement `get_queries_for_md(md_file_path)`: return all `queries` rows for a given MD source as a list of dicts
- [x] 3.6 Wire up CLI interface: `python db_logger.py [init | store <args> | get <md_path>]`

## 4. Implement `scripts/format_queries.py`

- [x] 4.1 Implement `extract_keywords(md_content)`: parse `## Keywords` section first; fall back to bold text and `##`/`###` headings if section absent; return a list of keyword strings
- [x] 4.2 Implement `build_wos_query(keywords)`: construct `TS=("kw1" AND "kw2" ...)` string; run balanced-parenthesis and illegal-character (`{`, `}`) validation
- [x] 4.3 Implement `build_scopus_query(keywords, exact=False)`: construct `TITLE-ABS-KEY("kw1" AND "kw2")` (default) or `TITLE-ABS-KEY({kw1} AND {kw2})` (exact mode); validate balanced parentheses and no wildcards inside curly braces
- [x] 4.4 Implement `build_flat_query(keywords)`: join first 10 keywords with spaces for Semantic Scholar, OpenAlex, CrossRef
- [x] 4.5 Implement `generate_all(md_file_path, exact_scopus=False, force=False)`: orchestrate extraction → build per-database queries → deduplication check → DB storage; return dict mapping database name → query string
- [x] 4.6 Wire up CLI interface: `python format_queries.py <md_file_path> [--exact-scopus] [--force]`; print results as JSON

## 5. Write `SKILL.md` Using `skill-creator` Workflow

- [x] 5.1 Invoke `skill-creator` to capture skill intent, write the structured `SKILL.md` with progressive disclosure (description, trigger phrases, input/output spec, step-by-step prompt rules, examples for each database)
- [x] 5.2 Add concrete example query outputs for WoS, Scopus (fuzzy + exact), Semantic Scholar, OpenAlex, CrossRef
- [x] 5.3 Include a "Keyword Extraction" section in `SKILL.md` documenting the two-tier extraction strategy (structured `## Keywords` first, then fallback)

## 6. Integration Verification

- [x] 6.1 Run `python db_logger.py init` on a clean environment (no `data/research.db`) — confirm DB is created from `assets/example.db` with all three tables
- [x] 6.2 Run `python format_queries.py data/papers/summaries/reversible\ hydropower_0525_summary.md` — confirm five query rows inserted into `data/research.db` and printed to stdout
- [x] 6.3 Re-run the same command without `--force` — confirm all five targets are skipped (deduplication working)
- [x] 6.4 Re-run with `--force` — confirm five new rows are inserted alongside existing ones
- [x] 6.5 Run against a hand-written MD file not present in `summaries` table — confirm `summary_id=NULL`, `md_file_path` populated
- [x] 6.6 Query `SELECT * FROM queries;` in SQLite and verify FK integrity (summary_id matches a real summaries row or is NULL)
- [x] 6.7 Verify the `/literature-query-generator` slash command appears in the IDE and can be triggered without errors

## 7. Commit

- [x] 7.1 Stage and commit all new files: skill directory, scripts, `assets/example.db`, workflow file
- [x] 7.2 Confirm `.gitignore` does not accidentally exclude `assets/example.db`

## 8. LLM-Based Keyword Extraction & Routing Refactoring

- [x] 8.1 Modify `format_queries.py` CLI parser to accept keyword arguments (e.g. `--keywords "kw1, kw2, kw3"` or multiple `--keyword` values)
- [x] 8.2 Update `format_queries.py` orchestration logic to use the provided keywords directly, bypassing the local `extract_keywords` heuristic when they are supplied
- [x] 8.3 Update `.agent/skills/literature-query-generator/SKILL.md` instructions:
  - Add input file format routing guidelines (MD vs. PDF/DOCX)
  - Detail how to check if a Markdown path exists in the `summaries` table to link `summary_id`
  - Detail how to delegate PDF/DOCX inputs to the `paper-summarizer` skill, capturing the generated summary card path, the `summary_id` logged in SQLite, and the summary content
  - Instruct the LLM to read the entire summary Markdown content, analyze its semantic context, synthesize optimal search keywords, and execute `format_queries.py` with the extracted keywords passed via CLI
- [x] 8.4 Update the workflow trigger `.agent/workflows/literature-query-generator.md` to support PDF and DOCX inputs and register updated routing logic, explicitly outlining the delegation steps to the `paper-summarizer` workflow
- [x] 8.5 Perform integration verification:
  - Run `format_queries.py` with custom `--keywords` and verify correct WoS/Scopus/flat formatting and correct storage in `data/research.db`
  - Verify that when no `--keywords` is passed, the script falls back to local heuristic extraction
  - Test MD lookup scenario: input an existing MD file, verify it links to the database `summary_id`
  - Test standalone MD scenario: input a non-existent MD path, verify it writes to DB with `summary_id = NULL` and relative path populated
  - Test PDF/DOCX delegation scenario: input a `.pdf`/`.docx` file, verify the agent routes it to `paper-summarizer`, generates the summary card, then builds and stores queries linked to the generated card's database record
- [x] 8.6 Commit updated script, `SKILL.md`, `literature-query-generator.md` workflow, and documentation changes

## 9. Latest Summary Run Alignment

- [x] 9.1 Refactor `resolve_summary_id()` in `db_logger.py` to query matching `summary_file_path` records sorted by `id DESC LIMIT 1` (ensuring lookup yields the most recent summary run)
- [x] 9.2 Update `.agent/skills/literature-query-generator/SKILL.md` instructions to specify that query linkage must always match the latest summary run record in summaries table
- [x] 9.3 Perform integration verification:
  - Re-run query builder for a document with multiple summaries rows (e.g. ID 1 and ID 2) and check that it resolves to the latest ID (ID 2) and does not skip query generation as duplicate (since queries for ID 2 are absent)
- [x] 9.4 Commit updated files and documentation changes
