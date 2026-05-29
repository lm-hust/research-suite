## Context

Researchers often need to extract key findings from many academic papers across multiple formats (PDF, DOCX, TXT, MD). Performing this manually is slow and error-prone. This change designs a structured, local, agentic summarization flow (`/paper-summarizer` slash command) that reads literature from `data/papers/`, extracts high-density structured facts (Motivation, Methodology, Evaluation, Limitations), outputs Markdown summaries to `data/papers/summaries/` and the chat window, and logs metadata into a SQLite database (`data/research.db`) with content hash deduplication.

## Goals / Non-Goals

**Goals:**
- Create `.agent/skills/paper-summarizer/SKILL.md` outlining the summarization workflow.
- Create supporting Python scripts to parse PDF (via `pdfplumber`) and DOCX (via `python-docx`) files in a layout-aware manner.
- Set up a normalized, granular dual-table SQLite database (`data/research.db`) containing `papers` and `summaries` tables.
- Compute SHA-256 file hashes to prevent duplicate processing of the same paper under different paths or names.
- Register the `/paper-summarizer` workflow slash command trigger.
- Conduct local testing and evaluation of the summarizer using the `skill-creator` meta-skill.

**Non-Goals:**
- Building a web-based GUI for summarization (the tool will run entirely inside the agent/IDE terminal).
- Scraping or automatically fetching papers from online paper repositories (the user must place papers in `data/papers/` manually).

## Decisions

### 1. File Parsing Utilities Selection
- **Decision**: Use `pdfplumber` for PDF parsing and `python-docx` for DOCX parsing.
- **Rationale**: Standard PDF parsers (like `PyPDF2` or `pypdf`) merge multi-column text horizontally, rendering academic paper text unreadable. `pdfplumber` extracts characters with visual coordinates, allowing layout-aware extraction to preserve columns and flow. `python-docx` is the standard for extracting paragraphs and tables from Word files.

### 2. Granular SQLite Schema Normalization
- **Decision**: Create a double-table schema (`papers` and `summaries`) connected via a foreign key, with `file_hash` as a UNIQUE constraint in the `papers` table.
- **Rationale**: Adhering to our Modular & Granular Design Rule, a single-table design would lead to redundant records if a file is renamed or relocated. By separating file identity (`papers` table, unique on content hash) from summary runs (`summaries` table, storing metadata and Markdown text), we ensure content-level de-duplication and a clean historical audit trail.

### 3. Isolation of Processing Logic
- **Decision**: Develop separate, modular Python helper scripts (`parse_pdf.py`, `parse_docx.py`, `db_logger.py`) under `.agent/skills/paper-summarizer/scripts/` instead of writing parsing/DB logic in raw shell or JavaScript commands.
- **Rationale**: Kept in line with granular design, this encapsulates low-level parsing and SQL queries into deterministic, testable Python scripts, keeping the main `SKILL.md` instructions focused on high-level orchestration, prompting, and quality grading.

### 4. Summary Caching and Auto-Regeneration
- **Decision**: If a document is already registered in the `papers` table, check if its physical Markdown card is present on the disk.
  - If present: Load and render it directly to save API tokens and time.
  - If missing: Auto-trigger re-summarization and log the new run.
- **Rationale**: This creates a robust, self-healing caching mechanism. If a user deletes a summary card manually, the system automatically regenerates it upon the next request. If the card is intact, it bypasses costly processing, preserving both local performance and LLM API resources.


## Risks / Trade-offs

- **Risk: Missing Environment Dependencies**
  - *Risk*: The host machine may lack the required Python libraries (`pdfplumber`, `python-docx`), causing the script to fail.
  - *Mitigation*: The agent skill will check for package imports first. If missing, it will automatically attempt to install them or print clear instructions for the user (`pip install pdfplumber python-docx`).

- **Risk: Content Hash Mismatch on Metadata Edits**
  - *Risk*: Changing minor metadata or renaming an external file will not affect the SHA-256 hash, but modifying the file content (e.g. adding annotations) will change the hash, creating a duplicate record for what is conceptually the same paper.
  - *Mitigation*: The `db_logger.py` will log both `file_path` and `file_hash` and perform upserts on matching paths or matching hashes, alerting the user about existing entries.
