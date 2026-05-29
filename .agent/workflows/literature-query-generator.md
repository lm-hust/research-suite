---
description: Generate syntactically validated Boolean search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any document path. This skill always delegates to paper-summarizer first to parse the document and verify its academic validity.
---

# Literature Query Generator Workflow

Generate validated academic search query strings for five major databases from any document file path.

---

**Input**: A path to a document file (Markdown `.md`, PDF `.pdf`, DOCX `.docx`, TXT `.txt`). Optionally specify `--exact-scopus` for Scopus exact-phrase mode, or `--force` to re-generate even if queries already exist.

**Steps**

1. **Precondition Database Check**:
   - Check if `data/research.db` exists and has the `queries` table. If not, delete `data/research.db` (if exists), copy `.agent/skills/paper-summarizer/assets/example.db` to `data/research.db`, and run a SQL statement to create the `queries` table.

2. **Delegate to Paper Summarizer**:
   - Call the `paper-summarizer` workflow on the input file path.
   - If the `paper-summarizer` workflow aborts or returns `false` due to academic validity check failure, abort this workflow immediately.
   - Otherwise, capture the resulting `summary_id` and `summary_content`.

3. **Database Query Cache Check**:
   - Query the `queries` table for pre-existing records matching the retrieved `summary_id` across the five target databases (unless `--force` is specified).
   - If queries for all 5 databases exist, bypass Step 4 and Step 5 entirely, directly retrieve the stored query strings, and proceed to Step 6.
   - If one or more database queries are missing, proceed to Step 4.

4. **Semantic Keyword Synthesis (LLM-driven)**:
   - Read the `summary_content`.
   - Use LLM to semantically analyze the concepts and synthesize 3-10 optimal search keywords.

5. **Generate and Store Queries**:
   - Execute the formatting script, passing the synthesized keywords via the `--keywords` parameter:
     ```bash
     python .agent/skills/literature-query-generator/scripts/format_queries.py <summary_id> --keywords "<comma_separated_keywords>" [--exact-scopus] [--force]
     ```

6. **Output**: Render the generated query strings in a formatted Markdown block in the chat window, indicating the associated summary ID.
