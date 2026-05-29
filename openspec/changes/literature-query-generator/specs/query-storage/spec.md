## ADDED Requirements

### Requirement: Persist generated queries to database
The skill SHALL write each generated query string to the `queries` table in `data/research.db`. One row SHALL be inserted per database target (WOS, Scopus, SemanticScholar, OpenAlex, CrossRef), totalling five rows per successful invocation.

#### Scenario: MD file is a known summary card
- **WHEN** the input Markdown file path matches one or more `summary_file_path` values in the `summaries` table
- **THEN** each inserted `queries` row SHALL have `summary_id` set to the *latest* matching `summaries.id` (i.e. the one with the highest ID value), and `md_file_path` SHALL be NULL

#### Scenario: MD file is hand-written (not in summaries table)
- **WHEN** the input Markdown file path does NOT match any `summary_file_path` in the `summaries` table
- **THEN** each inserted `queries` row SHALL have `summary_id` set to NULL and `md_file_path` set to the relative path of the input file

#### Scenario: Database file does not yet exist
- **WHEN** `data/research.db` is absent and `assets/example.db` exists in the skill's assets folder
- **THEN** the skill SHALL copy `assets/example.db` to `data/research.db` before proceeding, and SHALL then apply `CREATE TABLE IF NOT EXISTS` for `queries`

---

### Requirement: queries table schema
The `queries` table SHALL be created with the following columns if it does not already exist:

```sql
CREATE TABLE IF NOT EXISTS queries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id   INTEGER,
    md_file_path TEXT,
    database     TEXT NOT NULL,
    query_string TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (summary_id) REFERENCES summaries (id) ON DELETE SET NULL
)
```

#### Scenario: Table creation on init
- **WHEN** `db_logger.py init` is called
- **THEN** the `queries` table SHALL be created in `data/research.db` if it does not already exist, and all pre-existing tables (`papers`, `summaries`) SHALL remain unmodified

---

### Requirement: Existing tables must not be modified
The skill's `db_logger.py` SHALL use only `CREATE TABLE IF NOT EXISTS` for table creation. It SHALL NOT execute `ALTER TABLE`, `DROP TABLE`, or any DML against `papers` or `summaries`.

#### Scenario: Init on existing database
- **WHEN** `data/research.db` already exists with `papers` and `summaries` tables populated
- **THEN** running `db_logger.py init` SHALL add the `queries` table without altering or truncating any existing data
