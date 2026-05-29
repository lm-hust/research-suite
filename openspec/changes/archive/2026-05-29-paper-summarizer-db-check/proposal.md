## Why

If the SQLite database `data/research.db` is missing, or if its database schema or format is corrupted/invalid (e.g., missing required tables `papers` or `summaries`), execution of the `paper-summarizer` skill currently fails silently or throws database exceptions. Introducing a database check and fallback initialization as the very first step ensures robust execution and a self-healing environment.

## What Changes

- **Database Precondition Check**: The `paper-summarizer` skill will check for the existence and validity of `data/research.db` as its first step.
- **Example Database Fallback Copy**: If the database file is missing or invalid, the skill will delete any broken file, copy the template `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and then continue execution.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `paper-summarizer`: Add a database existence and validity check as the very first step, with automatic fallback to copy `example.db` if `research.db` is missing or invalid.

## Impact

- **Database**: Re-initializes `data/research.db` from `example.db` if the database is missing or corrupt.
- **Code**: Updates `db_logger.py` under the `paper-summarizer` skill to run `init_db()` safely at startup and verify schema validity.
