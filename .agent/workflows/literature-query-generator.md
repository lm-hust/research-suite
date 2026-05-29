---
description: Generate syntactically validated Boolean search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any Markdown summary file. Use this skill whenever the user wants to build search queries from a paper summary or MD notes, generate literature search strings, translate a summary into database queries, or find similar papers across academic databases.
---

# Literature Query Generator Workflow

Generate validated academic search query strings for five major databases from any Markdown file — whether produced by the `paper-summarizer` skill or hand-written notes.

---

**Input**: A path to a literature file (Markdown `.md`, PDF `.pdf`, or DOCX `.docx`). Optionally specify `--exact-scopus` for Scopus exact-phrase mode, or `--force` to re-generate even if queries already exist.

**Steps**

1. **Routing and Format Handling**:
   - **Case A: The input is a PDF or DOCX file**:
     - Delegate to the `paper-summarizer` workflow to parse the paper, generate a structured Markdown card, and log it to SQLite.
     - If the `paper-summarizer` workflow aborts or returns `false` due to the document not being a research/academic-related publication, abort this workflow immediately.
     - Otherwise, capture the resulting `summary_id` and Markdown content.
   - **Case B: The input is a Markdown file**:
     - Normalize path and check if it already exists in the summaries database table. If so, retrieve its `summary_id`; otherwise, set `summary_id` to `null`.
2. **Semantic Keyword Synthesis (LLM-driven)**:
   - Read the entire Markdown summary content.
   - Use LLM capability to semantically analyze the document's concepts and synthesize 3-10 optimal search keywords/phrases.
3. **Generate and Store Queries**:
   - Execute the formatting script, passing the synthesized keywords via the `--keywords` parameter:
     ```bash
     python .agent/skills/literature-query-generator/scripts/format_queries.py "<md_file_path>" --keywords "<comma_separated_keywords>" [--exact-scopus] [--force]
     ```
   - This script generates, validates, and stores queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef.
4. **Output**: Render the generated query strings in a formatted Markdown block in the chat window, grouped by database, indicating the associated summary ID.
