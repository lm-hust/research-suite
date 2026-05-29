# paper-summarizer Specification

## Purpose
TBD - created by archiving change paper-summarizer. Update Purpose after archive.
## Requirements
### Requirement: Supported File Formats & Parsing Routing
The system SHALL support PDF, DOCX, TXT, and MD formats. It SHALL route the files to appropriate parser scripts and output normalized layout text.

#### Scenario: Routing PDF files
- **WHEN** the user runs the summarizer on a PDF file
- **THEN** the system SHALL invoke the PDF parser script utilizing `pdfplumber` to extract text coordinates and maintain multi-column reading order

#### Scenario: Routing DOCX files
- **WHEN** the user runs the summarizer on a DOCX file
- **THEN** the system SHALL invoke the DOCX parser script utilizing `python-docx` to extract text paragraphs and tables

#### Scenario: Reading raw text files
- **WHEN** the user runs the summarizer on a TXT or MD file
- **THEN** the system SHALL read the content directly without calling external parsing scripts

### Requirement: High-Density Fact Extraction & Card Output
The system SHALL extract motivation, novel methodology, evaluation data, and limitations from the literature, and generate a standardized Markdown summary card.

#### Scenario: Successful academic fact extraction
- **WHEN** the paper text is analyzed by the agent
- **THEN** the system SHALL produce a Markdown card outlining Motivation, Methodology, Evaluation Data, and Limitations, displaying it in the chat window and writing it to `data/papers/summaries/<filename>_summary.md`

### Requirement: Granular SQLite Storage & Deduplication
The system SHALL record analysis metadata and Markdown cards in a double-table SQLite schema under `data/research.db`, preventing duplicate processing using SHA-256 content hashes and caching summaries.

#### Scenario: New paper ingestion
- **WHEN** a document with a unique content hash is parsed
- **THEN** the system SHALL insert its path and content hash into the `papers` table, and write its extracted metadata and Markdown card content into the `summaries` table

#### Scenario: Summarization bypass when summary file exists
- **WHEN** a paper with an already existing content hash is requested, and its corresponding Markdown summary file exists on the filesystem
- **THEN** the system SHALL bypass text extraction and AI summarization, read the existing Markdown summary file, and display it in the chat window

#### Scenario: Summarization re-generation when summary file is missing
- **WHEN** a paper with an already existing content hash is requested, but its corresponding Markdown summary file is missing on the filesystem
- **THEN** the system SHALL re-run text extraction, perform AI summarization, write the new Markdown card to the filesystem, and log the new run in the `summaries` table

### Requirement: Database Check and Fallback Initialization
Before initiating execution, the system SHALL check if the database file `data/research.db` exists and contains the required schema tables (`papers` and `summaries`). If `data/research.db` does not exist, or if it exists but lacks the required tables, the system SHALL remove the invalid file (if present) and copy the fallback template `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db` before proceeding with the hash check or extraction.

#### Scenario: Database file is missing or lacks required tables
- **WHEN** the `paper-summarizer` skill starts and `data/research.db` is missing or does not contain `papers` or `summaries` tables
- **THEN** the system SHALL remove the invalid file if present, copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and then proceed

