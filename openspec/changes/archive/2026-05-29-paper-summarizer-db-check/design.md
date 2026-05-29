## Context

The `paper-summarizer` skill logs paper metadata and analysis summaries in a SQLite database at `data/research.db`. If this file is missing, corrupt, or has an incorrect schema, python scripts that query or write to it will throw exceptions. We need to add a check at startup to guarantee database existence and valid schemas.

## Goals / Non-Goals

**Goals:**
- Perform a schema and database check as the first step of any database operation in `paper-summarizer`.
- Automatically recover from a missing or corrupt database by copying the clean seed database `example.db` from `.agent/skills/paper-summarizer/assets/example.db`.

**Non-Goals:**
- Backing up or migrating data from a corrupt database.
- Modifying the tables or columns in the `example.db` schema.

## Decisions

### Decision 1: Perform the check during `init_db()` in `db_logger.py`
**Choice:** Add check-and-copy logic directly within `init_db()` in `.agent/skills/paper-summarizer/scripts/db_logger.py`.
**Rationale:** `init_db()` is already called at the start of `check_hash()` and `log_summary()`. Placing the logic here guarantees that the check is run before any database operation without duplicating check logic in multiple script files or command-line scripts.

### Decision 2: Schema validation criteria
**Choice:** Verify if both the `papers` and `summaries` tables exist and can be queried. If not, delete the corrupt database file and re-copy the seed `example.db`.
**Rationale:** SQLite `sqlite_master` table queries can easily confirm table presence. If either table is missing, the database is considered corrupt and is replaced.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Deleting a corrupt database loses user summary history | The user's summary cards still exist under `data/papers/summaries/`. If the database is recreated, those cards will be re-logged on subsequent runs because `check-hash` will detect that the Markdown file exists and can trigger regeneration/re-logging if needed. |
