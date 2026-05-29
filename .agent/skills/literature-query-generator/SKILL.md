---
name: literature-query-generator
description: Generate syntactically validated Boolean search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any Markdown file. Use this skill whenever the user wants to find similar papers, build literature search strings, translate a paper summary into database queries, or generate reproducible search expressions for academic databases. Trigger this skill even when the user just mentions "search for similar papers", "generate search queries", "find related literature", or "how do I search for this on Web of Science / Scopus / Semantic Scholar / OpenAlex / CrossRef".
---

# Literature Query Generator

Generate validated, database-specific search query strings from any Markdown file — whether produced by the `paper-summarizer` skill or hand-written notes.

Outputs ready-to-paste query strings for five databases, and persists them to `data/research.db` for reproducibility.

---

## Inputs

- **Required**: A path to a Markdown file (summary card or hand-written notes).
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

1. **Identify the input MD file** from the user's argument or prompt them to select from `data/papers/summaries/`.

2. **Run the query generation script**:
   ```
   python .agent/skills/literature-query-generator/scripts/format_queries.py <md_file_path> [--exact-scopus] [--force]
   ```

3. **Parse the JSON output** — it contains:
   - `_meta`: keywords extracted, summary_id link, flags used
   - `WOS`, `Scopus`, `SemanticScholar`, `OpenAlex`, `CrossRef`: each with `query` (success) or `error` / `skipped` (failure/duplicate)

4. **Render the queries** in a clean Markdown block in the chat:

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

> Keywords extracted: reversible hydropower, pumped storage, variable speed, ...
> Stored to `data/research.db` (queries table) ✓
```

5. **If `skipped: true`** appears for any database, inform the user queries already exist and suggest using `--force` to regenerate.

6. **If `error`** appears for any database, explain the validation issue and suggest fixing the keyword extraction or using `--exact-scopus` if curly braces were the problem.

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
