## ADDED Requirements

### Requirement: Database Schema
The system SHALL ensure the SQLite database schema contains a queries table properly linked to summaries.

#### Scenario: Database schema validation
- **WHEN** the database is initialized
- **THEN** the system SHALL create the `queries` table containing id, summary_id, database, query_string, and created_at fields, with a foreign key constraint linking to `summaries`.

### Requirement: Storage Flow
The system SHALL persist all generated query strings to the queries table.

#### Scenario: Persist queries
- **WHEN** query generation succeeds
- **THEN** the system SHALL write 5 query rows (one per database) linked to `summary_id`.

### Requirement: Database Check and Replacement Precondition
The system SHALL verify and initialize the database as a precondition before execution.

#### Scenario: Database lacks queries table
- **WHEN** `data/research.db` is missing, OR it exists but does NOT contain the `queries` table
- **THEN** the system SHALL delete the existing database file (if present), copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and programmatically create the `queries` table inside it before executing.

#### Scenario: Database contains queries table
- **WHEN** `data/research.db` already contains the `queries` table
- **THEN** the system SHALL proceed to execute without modifying the database file.
