---
name: literature-query-generator
description: Generate validated academic search queries for Web of Science, Scopus, Semantic Scholar, OpenAlex, and CrossRef from any document path. This skill always delegates to paper-summarizer first to parse the document and verify its academic validity.
---

# Literature Query Generator

Generate validated search queries for academic databases from any document (PDF, DOCX, MD, TXT).

---

## Inputs & Outputs

### Inputs
- **Required**: A path to a document file (`.pdf`, `.docx`, `.md`, `.txt`).
- **Optional flags**:
  - `--exact-scopus` — Use Scopus exact-phrase mode.
  - `--force` — Re-generate queries even if they already exist in the database.

---

## Steps

1. **Academic Check & Summary Generation**:
   - Call the `paper-summarizer` skill on the input document path.
   - If the `paper-summarizer` skill returns `false` or aborts with an error (e.g. non-academic document), abort this skill execution immediately.
   - Otherwise, retrieve the `summary_id` and `summary_content` from the `paper-summarizer` run output.

2. **Semantic Keyword Synthesis (LLM-driven)**:
   - Read the `summary_content` returned by the summarizer.
   - Use LLM capability to analyze the document's concepts and synthesize 3-10 optimal search keywords/phrases.

3. **Format and Store Queries**:
   - Run the formatting script to generate and store queries in the database linked directly to the `summary_id`:
     ```bash
     python .agent/skills/literature-query-generator/scripts/format_queries.py <summary_id> --keywords "<comma_separated_keywords>" [--exact-scopus] [--force]
     ```

4. **Output Results**:
   - Format the queries in a clean Markdown block:

```markdown
## 🔍 Search Queries

### Web of Science
```
TS=("term1" AND "term2")
```

### Scopus
```
TITLE-ABS-KEY("term1" AND "term2")
```

### Semantic Scholar / OpenAlex / CrossRef
```
term1 term2 ...
```

> Keywords synthesized: term1, term2, ...
> Stored to `data/research.db` (queries table) linked to summary ID: <summary_id> ✓
```
