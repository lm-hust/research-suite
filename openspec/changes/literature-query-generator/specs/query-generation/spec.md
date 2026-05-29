## ADDED Requirements

### Requirement: Input File Format Routing and Integration
The skill SHALL support input file path routing based on format:
1. If the input is a Markdown (`.md`) file, it SHALL check if it matches an existing summary in the database.
2. If the input is a PDF (`.pdf`) or DOCX (`.docx`) file, it SHALL first run the `paper-summarizer` skill to generate a summary card, then generate queries from it.

#### Scenario: Existing Markdown summary input
- **WHEN** the input file is a Markdown (`.md`) file and its normalized path already exists in `summaries.summary_file_path`
- **THEN** the skill SHALL generate queries from its content and persist them to `queries` linked to the existing `summary_id`

#### Scenario: Standalone/Handwritten Markdown input
- **WHEN** the input file is a Markdown (`.md`) file and its normalized path does NOT exist in `summaries.summary_file_path`
- **THEN** the skill SHALL generate queries from its content and persist them to `queries` with `summary_id` set to `NULL` (and `md_file_path` set to the relative file path)

#### Scenario: PDF or DOCX input paper
- **WHEN** the input file has a `.pdf` or `.docx` extension
- **THEN** the skill SHALL invoke the `paper-summarizer` skill, retrieve the resulting summary's `summary_id` and Markdown content, generate queries from that content, and persist them linked to the retrieved `summary_id`

---

### Requirement: LLM-Based Semantic Keyword Extraction
The skill SHALL read the entire content of the Markdown file (either the existing/provided file, or the newly generated summary from the parser) and use the LLM to semantically analyze, select, and synthesize the most relevant search keywords.

#### Scenario: Agent reads entire MD content for context
- **WHEN** keyword generation is triggered
- **THEN** the LLM SHALL read the entire Markdown content, analyze its context, and select the optimal set of search keywords

#### Scenario: Passing keywords to CLI script
- **WHEN** the agent runs the query generator script
- **THEN** the agent SHALL pass the semantically-derived keywords via the `--keywords` parameter (comma-separated) to bypass local heuristic extraction

#### Scenario: Script fallback when keywords parameter is absent
- **WHEN** the script is run without the `--keywords` parameter
- **THEN** it SHALL fall back to local heuristic extraction (parsing `## Keywords`, bold text, and headings) for backward compatibility

#### Scenario: Empty or unreadable file
- **WHEN** the input file is empty or cannot be read
- **THEN** the skill SHALL exit with an error and SHALL NOT write any queries to the database

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
