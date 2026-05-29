# query-deduplication Specification

## Purpose
TBD - created by archiving change literature-query-generator. Update Purpose after archive.
## Requirements
### Requirement: Skip duplicate insertions
To avoid redundant database entries, the system SHALL skip inserting a new query if a row with the same `(summary_id, database)` already exists.

#### Scenario: Duplicate check
- **WHEN** a row already exists in `queries` with the same `(summary_id, database)`
- **THEN** the system SHALL skip insertion.

### Requirement: Force regeneration flag
The system SHALL support forcing query regeneration to bypass deduplication checks.

#### Scenario: Bypassing duplication
- **WHEN** the `--force` flag is provided
- **THEN** the system SHALL bypass deduplication and insert new rows.

### Requirement: Database Query Cache Check Short-Circuiting
The system SHALL short-circuit query generation if all five database queries already exist in the cache.

#### Scenario: All five database queries exist in cache
- **WHEN** the `queries` table already has entries for all five target databases linked to `summary_id`, AND the `--force` flag is NOT provided
- **THEN** the system SHALL short-circuit, bypass LLM synthesis and format script execution, and directly retrieve and output the queries from the database.

#### Scenario: Stale cache or incomplete databases
- **WHEN** one or more target database queries are missing for `summary_id`, OR the `--force` flag is provided
- **THEN** the system SHALL run LLM keyword synthesis and query formatting.

