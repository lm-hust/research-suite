## Why

Currently, researchers need to digest large volumes of scientific literature across multiple formats (PDF, DOCX, TXT, MD) and extract high-density core facts (such as research motivation, novel methodologies, experimental evaluation data, and critical limitations) to serve as standardized "seed" information for downstream LLM retrieval of similar publications. This change introduces a general-purpose, structured paper summarization skill in the workspace to automate this extraction process.

## What Changes

- Add a custom agent skill `.agent/skills/paper-summarizer/SKILL.md` defining the high-density extraction rules and dynamic paradigm adaptation.
- Utilize the `skill-creator` meta-skill to interactively design, author, test, and optimize the `paper-summarizer` skill via structured evaluations (evals) and description tuning.
- Add a custom workflow trigger `.agent/workflows/paper-summarizer.md` to register the `/paper-summarizer` slash command in the IDE.
- Implement supporting Python scripts to extract text and structure from PDF (via `pdfplumber`) and DOCX (via `python-docx`) files.
- Implement a SQLite database logger under `data/research.db` with a modular, granular schema consisting of two tables:
  - `papers`: To store file paths, names, and content hashes (SHA-256) for de-duplication.
  - `summaries`: To store generated summaries, structured metadata (title, authors, year, motivation, methods, eval data, limitations), and creation timestamps.
- Ensure summaries are both written to `data/papers/summaries/<filename>_summary.md` and printed in the chat window.
- Implement conditional bypass and re-generation caching logic: if a paper hash is already in the database and its Markdown file exists locally, display it directly without processing. If the Markdown file has been deleted, re-run text extraction and summarization, regenerate the Markdown card, and log the new run.

## Capabilities

### New Capabilities
- `paper-summarizer`: High-density scientific literature extraction, parsing, granular database logging, and structured card generation.

### Modified Capabilities
<!-- None -->

## Impact

- Establishes a unified `data/papers/` directory structure for literature files and summaries.
- Introduces new local Python script utilities under `.agent/skills/paper-summarizer/scripts/` to handle file parsing and database upserts.
- Requires installing `pdfplumber` and `python-docx` Python packages in the local environment.
- Adds new slash command `/paper-summarizer` to the agent workspace.
- Requires configuring a local evaluation environment under `.agent/skills/paper-summarizer/evals/` for the skill-creator.
