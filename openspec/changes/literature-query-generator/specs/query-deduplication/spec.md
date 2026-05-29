## ADDED Requirements

### Requirement: Skip duplicate query generation
The skill SHALL check for an existing row in the `queries` table before inserting a new one. The uniqueness key SHALL be the combination of the resolved MD source identifier and the target database name.

The resolved MD source identifier is defined as:
- `summary_id` (if the MD file matches a summaries row), OR
- `md_file_path` (if the MD file is hand-written and `summary_id` is NULL)

#### Scenario: Duplicate detected via summary_id
- **WHEN** a row already exists in `queries` with the same `summary_id` and `database`
- **THEN** the skill SHALL skip insertion for that database target and SHALL log a message indicating the duplicate was skipped

#### Scenario: Duplicate detected via md_file_path
- **WHEN** a row already exists in `queries` with `summary_id IS NULL` and the same `md_file_path` and `database`
- **THEN** the skill SHALL skip insertion for that database target and SHALL log a message indicating the duplicate was skipped

#### Scenario: No duplicate exists
- **WHEN** no existing row matches the uniqueness key for a given database target
- **THEN** the skill SHALL insert a new row for that target

---

### Requirement: Force re-generation flag
The skill SHALL support a `--force` flag that bypasses deduplication and inserts a fresh row regardless of existing entries.

#### Scenario: Force flag used on already-processed MD file
- **WHEN** the user invokes the skill with `--force` on an MD file that already has entries in `queries`
- **THEN** the skill SHALL insert new rows for all five database targets with a fresh `created_at` timestamp, leaving the prior rows intact (no update or delete)
