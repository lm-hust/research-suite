## 1. Foundation & Setup

- [x] 1.1 Create the local document storage directories `data/papers/` and `data/papers/summaries/`.
- [x] 1.2 Install necessary Python environment dependencies (`pdfplumber`, `python-docx`) in the local environment.

## 2. Supporting Python Parser Scripts

- [x] 2.1 Implement PDF parser script `parse_pdf.py` under `.agent/skills/paper-summarizer/scripts/` using `pdfplumber` to extract multi-column academic text.
- [x] 2.2 Implement DOCX parser script `parse_docx.py` under `.agent/skills/paper-summarizer/scripts/` using `python-docx` to extract text paragraphs and tables.
- [x] 2.3 Implement SQLite logger script `db_logger.py` under `.agent/skills/paper-summarizer/scripts/` to initialize `data/research.db` with dual tables (`papers` and `summaries`) and handle metadata de-duplication based on SHA-256 hashes.

## 3. Agent Skill & Workflow Definition

- [x] 3.1 Create `.agent/skills/paper-summarizer/SKILL.md` defining the fact extraction rules, Markdown card formatting template, database logging commands, and interactive folder listing.
- [x] 3.2 Create the workflow trigger `.agent/workflows/paper-summarizer.md` to register the `/paper-summarizer` command in the agent interface.

## 4. Evaluation & Optimization

- [x] 4.1 Place two representative academic papers (one PDF, one DOCX) under `data/papers/` for validation.
- [x] 4.2 Set up the local test configurations in `.agent/skills/paper-summarizer/evals/evals.json` defining evaluation prompts and assertions.
- [x] 4.3 Run benchmark runs using the `skill-creator` meta-skill to evaluate extraction quality and run database de-duplication tests.
- [x] 4.4 Apply description tuning to optimize triggering accuracy of the `/paper-summarizer` command.
- [x] 4.5 Implement conditional summary bypass and re-generation caching logic.
