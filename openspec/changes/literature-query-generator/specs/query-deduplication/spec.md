## Requirements: Query Deduplication

### Requirement: Skip duplicate insertions
- **Scenario: Duplicate check**
  - **WHEN** a row already exists in `queries` with the same `(summary_id, database)`
  - **THEN** skip insertion.

### Requirement: Force regeneration flag
- **Scenario: Bypassing duplication**
  - **WHEN** the `--force` flag is provided
  - **THEN** bypass deduplication and insert new rows.

### Requirement: Database Query Cache Check Short-Circuiting
- **Scenario: All five database queries exist in cache**
  - **WHEN** the `queries` table already has entries for all five target databases linked to `summary_id`, AND the `--force` flag is NOT provided
  - **THEN** the workflow SHALL short-circuit, bypass LLM synthesis and format script execution, and directly retrieve and output the queries from the database.
- **Scenario: Stale cache or incomplete databases**
  - **WHEN** one or more target database queries are missing for `summary_id`, OR the `--force` flag is provided
  - **THEN** the workflow SHALL run LLM keyword synthesis and query formatting.
