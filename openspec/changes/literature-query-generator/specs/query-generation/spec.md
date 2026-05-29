## Requirements: Query Generation

### Requirement: Always Delegate to Paper Summarizer First
The skill SHALL run `paper-summarizer` first for any input document.
- **Scenario: Delegation flow**
  - **WHEN** the user runs the literature query generator
  - **THEN** it SHALL call `paper-summarizer` and retrieve `summary_id` and `summary_content`
  - **WHEN** `paper-summarizer` aborts (e.g. invalid document)
  - **THEN** this skill SHALL abort immediately with `false` status and no output.

### Requirement: LLM Keyword Synthesis
- **WHEN** generating queries
- **THEN** the LLM SHALL read `summary_content` and extract 3-10 key terms.

### Requirement: Query Format Generation
- **Web of Science**: `TS=("term1" AND "term2")`
- **Scopus**: `TITLE-ABS-KEY("term1" AND "term2")` or `TITLE-ABS-KEY({term1} AND {term2})` (if exact mode)
- **Semantic Scholar / OpenAlex / CrossRef**: flat space-separated string of up to 10 terms.
