## ADDED Requirements

### Requirement: Database Check and Fallback Initialization
Before initiating execution, the system SHALL check if the database file `data/research.db` exists and contains the required schema tables (`papers` and `summaries`). If `data/research.db` does not exist, or if it exists but lacks the required tables, the system SHALL remove the invalid file (if present) and copy the fallback template `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db` before proceeding with the hash check or extraction.

#### Scenario: Database file is missing or lacks required tables
- **WHEN** the `paper-summarizer` skill starts and `data/research.db` is missing or does not contain `papers` or `summaries` tables
- **THEN** the system SHALL remove the invalid file if present, copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and then proceed
