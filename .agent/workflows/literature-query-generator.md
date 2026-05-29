---
description: Generate syntactically validated Boolean search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any Markdown summary file. Use this skill whenever the user wants to build search queries from a paper summary or MD notes, generate literature search strings, translate a summary into database queries, or find similar papers across academic databases.
---

# Literature Query Generator Workflow

Generate validated academic search query strings for five major databases from any Markdown file — whether produced by the `paper-summarizer` skill or hand-written notes.

---

**Input**: A path to a Markdown file (e.g., `@[data/papers/summaries/my_paper_summary.md]`). Optionally specify `--exact-scopus` for Scopus exact-phrase mode, or `--force` to re-generate even if queries already exist.

**Steps**

1. **Select the input MD file**: Accept the file path from the user's argument. If omitted, list available files in `data/papers/summaries/` for selection.
2. **Generate queries**: Run the format_queries script:
   ```
   python .agent/skills/literature-query-generator/scripts/format_queries.py <md_file_path> [--exact-scopus] [--force]
   ```
   This script:
   - Extracts keywords from the MD file (`## Keywords` section first; falls back to bold text and headings)
   - Builds per-database query strings (WoS, Scopus, Semantic Scholar, OpenAlex, CrossRef)
   - Validates syntax for each database
   - Checks for duplicates (skips if already generated, unless `--force` is used)
   - Persists results to `data/research.db` in the `queries` table
   - Prints results as JSON to stdout
3. **Output**: Render the generated query strings in a formatted Markdown block in the chat window, grouped by database.
