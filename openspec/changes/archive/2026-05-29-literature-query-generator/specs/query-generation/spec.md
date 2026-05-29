## ADDED Requirements

### Requirement: Always Delegate to Paper Summarizer First
The system SHALL delegate execution to the `paper-summarizer` first for any input document to verify academic validity and generate a summary.

#### Scenario: Delegation flow
- **WHEN** the user runs the literature query generator
- **THEN** it SHALL call `paper-summarizer` and retrieve `summary_id` and `summary_content`

#### Scenario: Summarizer aborts
- **WHEN** `paper-summarizer` aborts due to validation failure
- **THEN** the system SHALL abort immediately with `false` status.

### Requirement: LLM Keyword Synthesis
The system SHALL use the LLM to analyze the summary content and synthesize 3-10 optimal search keywords.

#### Scenario: Synthesis from summary
- **WHEN** generating queries
- **THEN** the LLM SHALL read `summary_content` and extract 3-10 key terms.

### Requirement: Query Format Generation
The system SHALL format the synthesized keywords into queries customized for each target database.

#### Scenario: WoS formatting
- **WHEN** formatting for Web of Science
- **THEN** the query SHALL be formatted as `TS=("term1" AND "term2")`

#### Scenario: Scopus formatting
- **WHEN** formatting for Scopus
- **THEN** the query SHALL be formatted as `TITLE-ABS-KEY("term1" AND "term2")` (or with curly braces in exact mode)

#### Scenario: Flat query formatting
- **WHEN** formatting for Semantic Scholar, OpenAlex, or CrossRef
- **THEN** the query SHALL be a flat space-separated string of up to 10 terms.
