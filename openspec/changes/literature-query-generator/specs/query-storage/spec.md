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
