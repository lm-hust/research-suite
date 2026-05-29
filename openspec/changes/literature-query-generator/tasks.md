# Tasks: Simplified Literature Query Generator

## 1. Clean up Old Code (To be done after exiting Explore Mode)
- [ ] 1.1 Delete the old skill folder `.agent/skills/literature-query-generator/`
- [ ] 1.2 Delete the old workflow file `.agent/workflows/literature-query-generator.md`

## 2. Re-Scaffold Simplified Skill
- [ ] 2.1 Create `.agent/skills/literature-query-generator/` directory with `__init__.py` and the new `SKILL.md`
- [ ] 2.2 Create `.agent/workflows/literature-query-generator.md` workflow trigger registering `/literature-query-generator`
- [ ] 2.3 Create `assets/example.db` containing the updated three-table schema (`papers`, `summaries`, `queries` where `queries.summary_id` is NOT NULL REFERENCES summaries(id) ON DELETE CASCADE)

## 3. Implement Simplified scripts/db_logger.py
- [ ] 3.1 Implement `init_db()`: check if `data/research.db` exists and has `queries` table. If not, delete it (if exists) and copy `assets/example.db` to seed the database.
- [ ] 3.2 Implement `check_duplicate(summary_id, database)`: Check duplicate strictly by `(summary_id, database)`
- [ ] 3.3 Implement `store_query(summary_id, database, query_string)`: Store queries linked to `summary_id`
- [ ] 3.4 Implement `get_queries_for_md(md_file_path)`: Find the latest `summary_id` from the path and get all query records associated with it
- [ ] 3.5 Expose simple CLI interface

## 4. Implement Simplified scripts/format_queries.py
- [ ] 4.1 CLI parser supporting `--keywords` parameter
- [ ] 4.2 Query builders for WoS, Scopus (fuzzy/exact), and flat engines (Semantic Scholar, OpenAlex, CrossRef)
- [ ] 4.3 Orchestrator logic that connects to the database via `db_logger.py` to check duplication and insert queries linked to the required `summary_id`

## 5. Write Simplified SKILL.md
- [ ] 5.1 Document the database check precondition and the direct delegation step: call `paper-summarizer` first for all files, check if it aborts, and extract output
- [ ] 5.2 Document the keyword synthesis and script execution steps

## 6. Verification
- [ ] 6.1 Verify delegation to `paper-summarizer` for PDF/DOCX and MD files
- [ ] 6.2 Verify that non-academic files abort early and generate no queries or database records
- [ ] 6.3 Verify deduplication and `--force` flag operations
- [ ] 6.4 Verify database check and copy precondition (when DB file is missing, or lacks queries table, verify it is replaced by example.db)
