---
description: High-density scientific literature extraction, parsing, granular database logging, and structured card generation
---

# Paper Summarizer Workflow

Summarize scientific papers across multiple formats, log metadata to the SQLite `data/research.db` database, and save standardized Markdown cards under `data/papers/summaries/`.

---

**Input**: The path to a document (PDF, DOCX, TXT, MD) or a file reference (e.g., `@[paper.pdf]`). If omitted, the summarizer lists available files in `data/papers/` for selection.

**Steps**

1. **Select the file**: Use direct argument or prompt the user with files found in `data/papers/`.
2. **De-duplication**: Compute content SHA-256 hash and run `python .agent/skills/paper-summarizer/scripts/db_logger.py check-hash <file_path>` to see if it is already analyzed. Prompt user for overwrite permission if found.
3. **Extract raw text**: Run python parser scripts:
   - For PDF: `python .agent/skills/paper-summarizer/scripts/parse_pdf.py <file_path>` (layout-aware, multi-column preservation).
   - For DOCX: `python .agent/skills/paper-summarizer/scripts/parse_docx.py <file_path>` (reconstructs paragraphs and tables in order).
   - For TXT / MD: Read directly.
4. **Academic Validity Check**: Determine if the extracted text represents a scientific, technical, or academic-related research paper or technical study document. If not, abort execution immediately (output `false`, do NOT generate any Markdown summary file, do NOT run `db_logger.py log` to insert into the database, print `Error: Input document is not a research or academic-related publication.` and exit).
5. **Extract key facts**: Summarize research motivation, methodology, evaluation data, and limitations. Extract metadata (Title, Authors, Year) strictly from the header/title page without guessing or hallucinating missing details from references/citations.
6. **Save and Log**:
   - Write formatted Summary Card to `data/papers/summaries/<filename>_summary.md`.
   - Run `python .agent/skills/paper-summarizer/scripts/db_logger.py log` to insert/update the dual-table database records in `data/research.db`.
7. **Output**: Render the generated Markdown card directly in the chat window.
