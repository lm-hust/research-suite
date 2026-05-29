"""
format_queries.py — literature-query-generator

Extracts keywords from a Markdown file and builds validated search query
strings for five academic databases:
  - WOS   : Web of Science  — TS=("kw1" AND "kw2")
  - Scopus : Scopus          — TITLE-ABS-KEY("kw1" AND "kw2") or with {}
  - SS     : Semantic Scholar — flat keyword phrase
  - OA     : OpenAlex        — flat keyword phrase
  - CR     : CrossRef        — flat keyword phrase

Usage:
    python format_queries.py <md_file_path> [--exact-scopus] [--force]

Prints a JSON object mapping database name → query string (or error).
Also persists results to data/research.db via db_logger.
"""
import sys
import os
import re
import json
import argparse

# Ensure scripts/ dir is on path when run as a script
sys.path.insert(0, os.path.dirname(__file__))
import db_logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATABASES = ["WOS", "Scopus", "SemanticScholar", "OpenAlex", "CrossRef"]
MAX_FLAT_KEYWORDS = 10


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

def extract_keywords(md_content: str) -> list:
    """Extract a list of search keyword strings from Markdown content.

    Strategy (two-tier):
    1. Look for a '## Keywords' section and parse its content as a
       comma/semicolon/newline-separated list.
    2. Fall back to collecting bold phrases (**text**) and section
       headings (## and ###) when no Keywords section is present.

    Returns a deduplicated list of non-empty strings, preserving order.
    """
    keywords = []

    # Tier 1: explicit Keywords section
    kw_match = re.search(
        r'(?:^|\n)#{1,4}\s*keywords?\s*\n(.*?)(?=\n#{1,4}\s|\Z)',
        md_content,
        re.IGNORECASE | re.DOTALL
    )
    if kw_match:
        block = kw_match.group(1)
        # Split on commas, semicolons, newlines, bullet markers
        raw = re.split(r'[,;\n]+', block)
        for item in raw:
            item = re.sub(r'^[\s\-\*\•]+', '', item).strip()
            # Strip markdown bold/italic
            item = re.sub(r'\*+', '', item).strip()
            if item:
                keywords.append(item)

    if keywords:
        return _deduplicate(keywords)

    # Tier 2: bold phrases then headings
    # Filter out metadata-style labels (short single-token labels like "Authors:", "Year:")
    # These appear in paper-summarizer cards but are not searchable concepts.
    METADATA_LABELS = {
        'file name', 'file path', 'authors', 'year', 'metadata',
        'author', 'date', 'doi', 'journal', 'volume', 'pages',
        'publisher', 'issn', 'isbn', 'url', 'source'
    }

    # Bold: **phrase** or __phrase__
    bold_matches = re.findall(r'\*\*(.+?)\*\*|__(.+?)__', md_content)
    for m in bold_matches:
        term = (m[0] or m[1]).strip()
        # Skip short metadata labels and terms with only punctuation/digits
        if term and term.lower() not in METADATA_LABELS and len(term) > 3:
            keywords.append(term)

    # Headings (##, ###) — skip the top-level title (#)
    heading_matches = re.findall(r'^#{2,3}\s+(.+)', md_content, re.MULTILINE)
    for h in heading_matches:
        term = h.strip()
        # Filter out common structural and metadata headings
        skip = {'keywords', 'abstract', 'introduction', 'conclusion',
                 'references', 'methodology', 'results', 'discussion',
                 'background', 'related work', 'acknowledgements',
                 'metadata', 'authors', 'year', 'file name', 'file path'}
        if term.lower() not in skip:
            keywords.append(term)

    return _deduplicate(keywords)


def _deduplicate(lst: list) -> list:
    seen = set()
    out = []
    for item in lst:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------

def _validate_balanced(query: str, open_char='(', close_char=')') -> bool:
    depth = 0
    for ch in query:
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def build_wos_query(keywords: list) -> dict:
    """Build a Web of Science TS= Boolean query.

    Format: TS=("kw1" AND "kw2" AND ...)
    Returns {'query': str} on success, {'error': str} on failure.
    """
    if not keywords:
        return {"error": "No keywords extracted"}

    terms = ' AND '.join(f'"{kw}"' for kw in keywords)
    query = f'TS=({terms})'

    # Validation: balanced parentheses, no curly braces
    if not _validate_balanced(query):
        return {"error": f"WOS query has unbalanced parentheses: {query}"}
    if '{' in query or '}' in query:
        return {"error": f"WOS query contains illegal characters: {query}"}

    return {"query": query}


def build_scopus_query(keywords: list, exact: bool = False) -> dict:
    """Build a Scopus TITLE-ABS-KEY Boolean query.

    Default (fuzzy) mode:  TITLE-ABS-KEY("kw1" AND "kw2")
    Exact mode:            TITLE-ABS-KEY({kw1} AND {kw2})

    In exact mode, wildcards (* ?) are stripped from terms.
    Returns {'query': str} on success, {'error': str} on failure.
    """
    if not keywords:
        return {"error": "No keywords extracted"}

    if exact:
        # Curly braces, no wildcards allowed
        cleaned = [re.sub(r'[*?]', '', kw) for kw in keywords]
        terms = ' AND '.join(f'{{{kw}}}' for kw in cleaned)
    else:
        terms = ' AND '.join(f'"{kw}"' for kw in keywords)

    query = f'TITLE-ABS-KEY({terms})'

    if not _validate_balanced(query):
        return {"error": f"Scopus query has unbalanced parentheses: {query}"}
    if not query.startswith("TITLE-ABS-KEY("):
        return {"error": f"Scopus query missing TITLE-ABS-KEY opener: {query}"}

    return {"query": query}


def build_flat_query(keywords: list) -> dict:
    """Build a space-separated flat keyword string (Semantic Scholar / OpenAlex / CrossRef).

    Uses at most MAX_FLAT_KEYWORDS terms.
    """
    if not keywords:
        return {"error": "No keywords extracted"}

    selected = keywords[:MAX_FLAT_KEYWORDS]
    return {"query": " ".join(selected)}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generate_all(md_file_path: str, exact_scopus: bool = False, force: bool = False, keywords_list: list = None) -> dict:
    """Generate and persist query strings for all five databases.

    Args:
        md_file_path: Path to the Markdown input file.
        exact_scopus: Use curly-brace exact mode for Scopus.
        force: Skip deduplication check and insert new rows.
        keywords_list: Optional pre-extracted keyword terms to use.

    Returns a dict mapping database name → {'query': str} or {'error': str}.
    """
    # Read MD file
    if not os.path.exists(md_file_path):
        return {db: {"error": f"File not found: {md_file_path}"} for db in DATABASES}

    if keywords_list:
        keywords = keywords_list
    else:
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return {db: {"error": "Markdown file is empty"} for db in DATABASES}

        # Extract keywords
        keywords = extract_keywords(content)

    if not keywords:
        return {db: {"error": "Could not extract or receive any keywords"} for db in DATABASES}

    # Build queries
    flat = build_flat_query(keywords)
    results = {
        "WOS": build_wos_query(keywords),
        "Scopus": build_scopus_query(keywords, exact=exact_scopus),
        "SemanticScholar": flat,
        "OpenAlex": flat,
        "CrossRef": flat,
    }

    # Resolve summary_id (None for hand-written MDs)
    summary_id = db_logger.resolve_summary_id(md_file_path)

    # Persist to DB (with deduplication)
    db_logger.init_db()
    for db_name, result in results.items():
        if "error" in result:
            continue  # Don't store failed queries

        if not force and db_logger.check_duplicate(summary_id, md_file_path, db_name):
            result["skipped"] = True
            result["reason"] = "duplicate"
            continue

        new_id = db_logger.store_query(
            summary_id, md_file_path, db_name, result["query"]
        )
        result["stored_id"] = new_id

    # Add metadata
    return {
        "_meta": {
            "md_file": md_file_path,
            "summary_id": summary_id,
            "keywords_extracted": keywords,
            "exact_scopus": exact_scopus,
            "force": force,
        },
        **results,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate academic database search queries from a Markdown file."
    )
    parser.add_argument("md_file_path", help="Path to the input Markdown file")
    parser.add_argument(
        "--exact-scopus",
        action="store_true",
        help="Use Scopus exact phrase mode (curly braces, no wildcards)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-generate and insert new rows even if duplicates exist",
    )
    parser.add_argument(
        "--keywords",
        help="Comma- or semicolon-separated list of keywords to use, bypassing heuristic extraction",
    )
    args = parser.parse_args()

    keywords_list = None
    if args.keywords:
        keywords_list = [
            k.strip() for k in re.split(r'[,;]+', args.keywords) if k.strip()
        ]

    output = generate_all(
        args.md_file_path,
        exact_scopus=args.exact_scopus,
        force=args.force,
        keywords_list=keywords_list
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
