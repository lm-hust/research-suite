## Requirements: Query Storage

### Requirement: Database Schema
The `queries` table in `data/research.db` SHALL have the following structure:
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

### Requirement: Storage Flow
- **Scenario: Persist queries**
  - **WHEN** query generation succeeds
  - **THEN** it SHALL write 5 query rows (one per database) linked to `summary_id`.

### Requirement: Database Check and Replacement Precondition
- **Scenario: Database lacks queries table**
  - **WHEN** `data/research.db` is missing, OR it exists but does NOT contain the `queries` table
  - **THEN** the workflow SHALL delete the existing database file (if present) and copy `assets/example.db` to `data/research.db` before executing or delegating to the `paper-summarizer` skill.
- **Scenario: Database contains queries table**
  - **WHEN** `data/research.db` already contains the `queries` table
  - **THEN** the workflow SHALL proceed to execute/delegate without modifying the database file.
