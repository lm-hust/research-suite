---
name: paper-summarizer
description: High-density scientific literature extraction, parsing, granular database logging, and structured card generation. Use this skill whenever the user mentions summarizing paper, parsing literature, running the /paper-summarizer command, or wants to extract facts from research publications (PDF, DOCX, TXT, MD).
---

# Paper Summarizer Skill

This skill automates layout-aware text extraction and high-density academic fact extraction (Motivation, Methodology, Evaluation, Limitations) from papers, logs results into the SQLite `data/research.db` database, and archives summary Markdown cards under `data/papers/summaries/`.

---

## Workflow Steps

### Step 1: Select the Literature File
1. **Direct Input**: If the user passed a path or referenced a file (e.g. `/paper-summarizer data/papers/example.pdf` or `/paper-summarizer @[paper.docx]`), use that file.
2. **Interactive Selection**: If no input is specified:
   - Check the directory `data/papers/` for any files with extensions `.pdf`, `.docx`, `.txt`, `.md`.
   - If no files are found, prompt the user: *"Please place your literature papers in the `data/papers/` directory and run the command again."*
   - If files are found, display a numbered list of files and ask the user to select one (e.g. *"Please select which file to summarize (enter index): 1. paper1.pdf, 2. paper2.docx"*). Wait for user input.

### Step 2: Content Hash De-duplication & Caching Check
Before parsing the file, run the `check-hash` command using the SQLite logger script to see if this document has already been analyzed:
```bash
python .agent/skills/paper-summarizer/scripts/db_logger.py check-hash "<path_to_paper>"
```
- **If the JSON response indicates `exists: true`**:
  - Retrieve the `summary_file_path` and `summary_file_exists` from the JSON response.
  - **Case A: The Markdown summary file EXISTS (`summary_file_exists` is `true`)**:
    - Bypass Step 3, Step 4, and Step 5 entirely.
    - Directly read the contents of the existing Markdown file.
    - Proceed to Step 6 to render it in the chat window.
  - **Case B: The Markdown summary file does NOT exist (`summary_file_exists` is `false`)**:
    - Inform the user: *"This paper was previously analyzed, but its Markdown summary card has been deleted. Automatically regenerating the summary..."*
    - Proceed to Step 3 to re-run text extraction, fact extraction, card writing, and database logging.

### Step 3: Run Text Extraction
Route the literature file to the correct parsing mechanism:
- **PDF File**: Execute the layout-aware parser:
  ```bash
  python .agent/skills/paper-summarizer/scripts/parse_pdf.py "<path_to_paper>"
  ```
- **DOCX File**: Execute the ordered docx parser:
  ```bash
  python .agent/skills/paper-summarizer/scripts/parse_docx.py "<path_to_paper>"
  ```
- **TXT / MD File**: Read the file contents directly.

### Step 4: High-Density Fact Extraction
Analyze the extracted text and extract the following structured details strictly from the document. Do NOT guess, extrapolate, or hallucinate metadata (such as authors or years) from references, citations, or external knowledge:
- **Title**: Academic paper title. If not explicitly stated, extract the main heading or use "Unknown".
- **Authors**: Authors list. Extract strictly from the author list or header. If not explicitly listed, use "Unknown". Do NOT guess or invent authors from citations, references, or footnotes.
- **Publication Year**: Calendar year of publication (integer, e.g., 2024). Extract strictly if explicitly stated. If not present, use `null` (or None). Do NOT guess based on references or citations.
- **Motivation**: Core motivation, research problem, and pain points addressed (2-3 sentences)
- **Methodology**: Main methodology, novel frameworks, or techniques introduced (2-3 sentences)
- **Evaluation Data**: Key datasets, experimental results, and metric comparisons (2-3 sentences)
- **Limitations**: Acknowledged limitations, caveats, or future work directions (2-3 sentences)

### Step 5: Save Markdown Card and Log to SQLite
1. Format the extracted facts into the standard Markdown Summary Card template (defined below).
2. Save the card to: `data/papers/summaries/<paper_basename>_summary.md` (replace extension with `_summary.md`).
3. Prepare the metadata JSON string containing keys: `title`, `authors`, `publication_year`, `motivation`, `methodology`, `evaluation_data`, `limitations`.
4. Log the summary run into the database by executing:
   ```bash
   python .agent/skills/paper-summarizer/scripts/db_logger.py log "<path_to_paper>" "data/papers/summaries/<paper_basename>_summary.md" '<metadata_json>'
   ```

### Step 6: Render Card in Chat
Output the Markdown Summary Card in full within the current chat window.

---

## Markdown Summary Card Template

ALWAYS write the summary card utilizing this exact template structure:

```markdown
# Literature Summary Card: [Title]

## Metadata
- **File Name**: [Name of file]
- **File Path**: [Path to file]
- **Authors**: [Authors]
- **Year**: [Publication Year]

## Motivation & Core Problem
[Detailed motivations and issues resolved by this work]

## Novel Methodology
[The key technical framework, design, or algorithms introduced]

## Experimental Evaluation & Metrics
[Key datasets, baselines, and performance metrics/data points achieved]

## Critical Limitations & Future Directions
[Limitations, assumptions, and future directions identified]
```
