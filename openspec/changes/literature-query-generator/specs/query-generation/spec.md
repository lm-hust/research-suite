## ADDED Requirements

### Requirement: Accept any Markdown file as input
The skill SHALL accept a path to any Markdown file as its sole required input. The file MAY be a structured summary card produced by `paper-summarizer` or an ad-hoc hand-written Markdown file. No specific front-matter or section structure SHALL be required.

#### Scenario: Structured summary card input
- **WHEN** the user provides a path to a Markdown file containing a `## Keywords` section
- **THEN** the skill SHALL extract keyword terms from that section and use them as the basis for all query strings

#### Scenario: Ad-hoc hand-written Markdown input
- **WHEN** the user provides a path to a Markdown file that does NOT contain a `## Keywords` section
- **THEN** the skill SHALL fall back to extracting terms from bold text (`**term**`) and section headings (`##` and `###`), and use those terms as the basis for query strings

#### Scenario: Empty or unreadable file
- **WHEN** the provided Markdown file is empty or cannot be read
- **THEN** the skill SHALL exit with an error message and SHALL NOT write any rows to the database

---

### Requirement: Generate Web of Science query string
The skill SHALL generate a query string conforming to Web of Science Advanced Search syntax.

#### Scenario: Single-concept WoS query
- **WHEN** one keyword term is extracted from the Markdown file
- **THEN** the generated WoS query SHALL have the form `TS=("term")`

#### Scenario: Multi-concept WoS query
- **WHEN** multiple keyword terms are extracted
- **THEN** the generated WoS query SHALL have the form `TS=("term1" AND "term2" AND ...)` with all terms enclosed in double quotes inside a single `TS=()` tag

#### Scenario: WoS query validation
- **WHEN** a WoS query string is generated
- **THEN** the system SHALL verify that parentheses are balanced and that no characters illegal in WoS (`{`, `}`) appear; if validation fails the system SHALL return an error and skip DB insertion

---

### Requirement: Generate Scopus query string
The skill SHALL generate a query string conforming to Scopus Advanced Search syntax.

#### Scenario: Scopus fuzzy phrase query (default)
- **WHEN** a Scopus query is generated using the default mode
- **THEN** all keyword phrases SHALL be wrapped in double quotes and enclosed in a single `TITLE-ABS-KEY(...)` field tag: `TITLE-ABS-KEY("term1" AND "term2")`

#### Scenario: Scopus exact phrase query (optional)
- **WHEN** the user requests exact-match mode for Scopus
- **THEN** all keyword phrases SHALL be wrapped in curly braces `{}` instead of double quotes: `TITLE-ABS-KEY({term1} AND {term2})`; no wildcard characters SHALL appear inside curly braces

#### Scenario: Scopus query validation
- **WHEN** a Scopus query string is generated
- **THEN** the system SHALL verify that parentheses are balanced and the `TITLE-ABS-KEY(` opener is present; if validation fails the system SHALL return an error and skip DB insertion

---

### Requirement: Generate flat keyword queries for Semantic Scholar, OpenAlex, and CrossRef
The skill SHALL generate a space-separated keyword phrase suitable for the simple search APIs of Semantic Scholar, OpenAlex, and CrossRef.

#### Scenario: Flat keyword phrase generation
- **WHEN** keyword terms are extracted from the Markdown file
- **THEN** the generated query for Semantic Scholar, OpenAlex, and CrossRef SHALL be a plain string of the most significant terms joined by spaces (e.g., `reversible hydropower pumped storage variable speed`)

#### Scenario: Long keyword list truncation
- **WHEN** more than 10 keyword terms are extracted
- **THEN** the skill SHALL use only the first 10 terms in the flat query to avoid overly narrow results
