# Research Suite

A high-density scientific literature extraction, parsing, and query generation assistant. It extracts metadata and core research facts from academic papers, stores summaries in an SQLite database (`data/research.db`), and generates validated search queries for major databases.

---

## ⚠️ Mandatory Development Environment

To prevent dependencies from polluting global system folders or relying on system-installed application environments, **all developers MUST set up and use a local Python virtual environment (`.venv`) inside this project directory.**

### Local Setup Instructions

#### 1. Initialize Virtual Environment
Run the following command in the project root directory:
```powershell
python -m venv .venv
```
*(If your default system `python` command is not configured, bootstrap it using a valid Python 3.12+ path).*

#### 2. Install Required Dependencies
With the virtual environment created, install the required packages using the local pip executable:
```powershell
.\.venv\Scripts\pip install pdfplumber python-docx
```

#### 3. Execution Standard
All agent workflows, custom scripts, and tool executions MUST run using the project-local Python executable:
- Python Path: `.\.venv\Scripts\python.exe`
- Pip Path: `.\.venv\Scripts\pip.exe`

---

## 🔍 Features & Workflows

### 1. Paper Summarizer
- Parses PDF and DOCX files with layout-aware structures.
- Performs academic validity checks.
- Generates high-density literature summary cards under `data/papers/summaries/`.
- Logs metadata to the SQLite database.

### 2. Literature Query Generator
- Synthesizes academic keywords from paper summaries.
- Formulates syntactically validated search queries for **Web of Science**, **Scopus**, **Semantic Scholar**, **OpenAlex**, and **CrossRef**.
