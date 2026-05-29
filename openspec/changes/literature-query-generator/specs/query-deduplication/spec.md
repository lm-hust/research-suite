## Requirements: Query Deduplication

### Requirement: Skip duplicate insertions
- **Scenario: Duplicate check**
  - **WHEN** a row already exists in `queries` with the same `(summary_id, database)`
  - **THEN** skip insertion.

### Requirement: Force regeneration flag
- **Scenario: Bypassing duplication**
  - **WHEN** the `--force` flag is provided
  - **THEN** bypass deduplication and insert new rows.
