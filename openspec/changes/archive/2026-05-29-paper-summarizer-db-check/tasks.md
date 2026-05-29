## 1. Implement Database Schema Verification & Fallback

- [x] 1.1 Update `init_db()` in `.agent/skills/paper-summarizer/scripts/db_logger.py` to query `sqlite_master` and verify the presence of both `papers` and `summaries` tables.
- [x] 1.2 Implement fallback copying: if the database file is missing or invalid, delete the file if present and copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db` first.

## 2. Update Documentation

- [x] 2.1 Update `.agent/skills/paper-summarizer/SKILL.md` to document this database check and copy fallback as the very first step in the workflow.

## 3. Verification

- [x] 3.1 Verify behavior when `data/research.db` is completely missing: ensure it gets copied and initialized correctly on execution.
- [x] 3.2 Verify behavior when `data/research.db` exists but is invalid (e.g. missing `summaries` table): ensure it gets removed, replaced, and initialized on execution.
