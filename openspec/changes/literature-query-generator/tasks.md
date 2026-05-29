# Tasks: Simplified Literature Query Generator

## 1. Clean up Old Code
- [x] 1.1 Delete the old skill folder `.agent/skills/literature-query-generator/`
- [x] 1.2 Delete the old workflow file `.agent/workflows/literature-query-generator.md`

## 2. Re-Scaffold Simplified Skill
- [x] 2.1 Create `.agent/skills/literature-query-generator/` directory with `__init__.py` and the new `SKILL.md`
- [x] 2.2 Create `.agent/workflows/literature-query-generator.md` workflow trigger registering `/literature-query-generator`

## 3. Implement Simplified scripts/db_logger.py
- [x] 3.1 Implement `init_db()`: check if `data/research.db` exists and has `queries` table. If not, delete it (if exists), copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and run the SQL statement to create the `queries` table.
- [x] 3.2 Implement `check_duplicate(summary_id, database)`: Check duplicate strictly by `(summary_id, database)`
- [x] 3.3 Implement `store_query(summary_id, database, query_string)`: Store queries linked to `summary_id`
- [x] 3.4 Implement `get_queries_for_md(md_file_path)`: Find the latest `summary_id` from the path and get all query records associated with it
- [x] 3.5 Expose simple CLI interface

## 4. Implement Simplified scripts/format_queries.py
- [x] 4.1 CLI parser supporting `--keywords` parameter
- [x] 4.2 Query builders for WoS, Scopus (fuzzy/exact), and flat engines (Semantic Scholar, OpenAlex, CrossRef)
- [x] 4.3 Orchestrator logic that connects to the database via `db_logger.py` to check duplication and insert queries linked to the required `summary_id`

## 5. Write Simplified SKILL.md
- [x] 5.1 Document the database check precondition and the direct delegation step: call `paper-summarizer` first for all files, check if it aborts, and extract output
- [x] 5.2 Document the keyword synthesis and script execution steps

## 6. Verification
- [x] 6.1 Verify delegation to `paper-summarizer` for PDF/DOCX and MD files
- [x] 6.2 Verify that non-academic files abort early and generate no queries or database records
- [x] 6.3 Verify deduplication and `--force` flag operations
- [x] 6.4 Verify database check and copy precondition (when DB file is missing, or lacks queries table, verify it is replaced by example.db)
