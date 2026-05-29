---
name: literature-query-generator
description: Generate syntactically validated Boolean search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any Markdown file, PDF, or DOCX paper. Use this skill whenever the user wants to find similar papers, build literature search strings, translate a paper summary into database queries, or generate reproducible search expressions for academic databases. Trigger this skill even when the user just mentions "search for similar papers", "generate search queries", "find related literature", or "how do I search for this on Web of Science / Scopus / Semantic Scholar / OpenAlex / CrossRef".
---

# Literature Query Generator

Generate validated, database-specific search query strings from any literature file (Markdown summaries, PDF, or DOCX papers).

Outputs ready-to-paste query strings for five databases, and persists them to `data/research.db` for reproducibility.

---

## Inputs

- **Required**: A path to a literature file. Supported formats:
  - Markdown (`.md`): Structured summary card or hand-written notes.
  - PDF (`.pdf`): Raw academic paper.
  - Word Document (`.docx`): Raw academic paper.
- **Optional flags**:
  - `--exact-scopus` — Use Scopus exact-phrase mode (curly braces `{}` instead of double quotes; no wildcards).
  - `--force` — Re-generate queries even if they already exist in the database.

---

## Keyword Extraction (Two-Tier Strategy)

The script extracts keywords automatically. Understanding how helps you write better input files.

**Tier 1 — Structured `## Keywords` section (preferred)**
If the Markdown file contains a heading like `## Keywords` or `## Key Terms`, the content under it is parsed as a comma/semicolon/newline-separated list. This is the most reliable mode.

```markdown
## Keywords
reversible hydropower, pumped storage, variable speed, carbon neutrality, energy storage
```

**Tier 2 — Fallback: bold text + section headings**
If no `## Keywords` section exists, the script scans for:
- `**bold phrases**` — typically the most important concepts in structured summary cards
- `## Sub-headings` and `### Sub-sub-headings` — excluding generic structural names like "Abstract", "Introduction", "References"

For best results with hand-written notes, add a `## Keywords` section.

---

## Query Formats by Database

### Web of Science
- Field tag: `TS=` (searches Title + Abstract + Author Keywords)
- Phrases: wrapped in double quotes `""`
- Format: `TS=("term1" AND "term2" AND "term3")`
- Validation: balanced parentheses; `{` and `}` are illegal

**Example:**
```
TS=("reversible hydropower" AND "pumped storage" AND "carbon neutrality" AND "energy storage")
```

### Scopus
- Field tag: `TITLE-ABS-KEY(...)` (searches Title + Abstract + Keywords)
- **Default (fuzzy) mode**: double quotes — allows plural/variant matching
  ```
  TITLE-ABS-KEY("reversible hydropower" AND "pumped storage" AND "carbon neutrality")
  ```
- **Exact mode** (`--exact-scopus`): curly braces — exact character match, no wildcards
  ```
  TITLE-ABS-KEY({reversible hydropower} AND {pumped storage} AND {carbon neutrality})
  ```
- Validation: balanced parentheses; `TITLE-ABS-KEY(` opener must be present

### Semantic Scholar / OpenAlex / CrossRef
- Format: space-separated flat keyword phrase (up to 10 terms)
- Suitable for these databases' simple search APIs

**Example:**
```
reversible hydropower pumped storage variable speed carbon neutrality energy storage
```

---

## Steps

1. **Routing and Format Handling**:
   Identify the input file format:
   - **Case A: The input is a PDF (`.pdf`) or DOCX (`.docx`) file**:
     - Automatically trigger/delegate to the `paper-summarizer` skill on the paper path first.
     - If the `paper-summarizer` skill returns `false` or aborts with an error indicating the input document is not a research/academic-related document, immediately abort this workflow and do not generate queries.
     - Otherwise, capture the generated summary's Markdown content and the newly logged `summary_id` from the summarizer run output.
     - Proceed to Step 2 using the newly generated Markdown file path.
   - **Case B: The input is a Markdown (`.md`) file**:
     - Check if the Markdown file path exists in the database `summaries` table (querying the `summary_file_path` column).
     - If it exists, capture its latest matched `id` (the highest ID value) as the `summary_id`.
     - If it does not exist (standalone/handwritten MD), the `summary_id` will be `null`.
     - Proceed to Step 2 using this Markdown file path.

2. **Semantic Keyword Synthesis (LLM-Driven)**:
   - Read the entire Markdown summary content (either the existing file, or the newly generated summary card).
   - Use LLM capability to analyze the document's context, research goals, methods, and findings.
   - Synthesize a set of high-relevance search keywords/phrases (typically 3 to 10 terms) that best represent the paper for literature retrieval. Do not rely on local regex/heading heuristics.

3. **Execute Query Generation and Storage**:
   - Run the formatting script, passing the normalized Markdown file path and the LLM-derived keywords (comma-separated) via the `--keywords` parameter:
     ```bash
     python .agent/skills/literature-query-generator/scripts/format_queries.py "<md_file_path>" --keywords "<comma_separated_keywords>" [--exact-scopus] [--force]
     ```
     *(Note: Always wrap paths and keywords in double quotes to handle spaces correctly).*

4. **Parse JSON Output**:
   - Parse the JSON output printed by the script. If the query already exists, the script will output `"skipped": true` (unless `--force` was used).

5. **Render Results in Chat**:
   - Format the queries in a clean Markdown output for the user:

```markdown
## 🔍 Search Queries

### Web of Science
\`\`\`
TS=("reversible hydropower" AND "pumped storage" AND ...)
\`\`\`

### Scopus
\`\`\`
TITLE-ABS-KEY("reversible hydropower" AND "pumped storage" AND ...)
\`\`\`

### Semantic Scholar / OpenAlex / CrossRef
\`\`\`
reversible hydropower pumped storage variable speed ...
\`\`\`

> Keywords synthesized: reversible hydropower, pumped storage, variable speed, ...
> Stored to `data/research.db` (queries table) linked to summary ID: <summary_id_or_NULL> ✓
```

6. **If `skipped: true`** appears for any database, inform the user queries already exist and suggest using `--force` to regenerate.

7. **If `error`** appears for any database, explain the validation issue.

---

## Scientific Rigor Rule

**Never guess or hallucinate keywords.** Only use terms explicitly present in the Markdown file. If the file is empty or unreadable, report an error — do not fabricate search terms.

---

## Database Schema

Results are stored in `data/research.db`:

```sql
queries (
    id           INTEGER PRIMARY KEY,
    summary_id   INTEGER,      -- NULL for hand-written MDs
    md_file_path TEXT,         -- relative path, populated when summary_id is NULL
    database     TEXT,         -- WOS / Scopus / SemanticScholar / OpenAlex / CrossRef
    query_string TEXT,
    created_at   TIMESTAMP
)
```

When the input MD is a summary card tracked in the `summaries` table, `summary_id` links back to it (and transitively to `papers`). For hand-written MDs, `summary_id` is NULL and `md_file_path` serves as the source reference.
