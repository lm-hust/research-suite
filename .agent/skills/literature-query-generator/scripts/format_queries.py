"""
format_queries.py — literature-query-generator

Generates syntactically validated search queries from keywords,
stores them in SQLite, and outputs them as JSON.
"""
import sys
import argparse
import json
import re
import os

# Import db_logger functions directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db_logger


def sanitize_term(term: str) -> str:
    """Strip quotes and leading/trailing spaces from a keyword term."""
    t = term.strip()
    # Strip quotes if term is wrapped in them
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        t = t[1:-1].strip()
    return t


def build_wos_query(keywords: list) -> str:
    """Format Web of Science Advanced Search query."""
    sanitized = [sanitize_term(k) for k in keywords if sanitize_term(k)]
    if not sanitized:
        return ""
    terms_str = " AND ".join(f'"{k}"' for k in sanitized)
    query = f"TS=({terms_str})"

    # Validate
    if query.count("(") != query.count(")"):
        raise ValueError("Balanced parentheses validation failed for Web of Science query.")
    if "{" in query or "}" in query:
        raise ValueError("Illegal curly braces found in Web of Science query.")

    return query


def build_scopus_query(keywords: list, exact: bool = False) -> str:
    """Format Scopus Advanced Search query."""
    sanitized = [sanitize_term(k) for k in keywords if sanitize_term(k)]
    if not sanitized:
        return ""

    if exact:
        # Exact-phrase mode: wrapped in curly braces
        for k in sanitized:
            if "*" in k or "?" in k:
                raise ValueError("Wildcards are not permitted inside Scopus exact curly braces.")
        terms_str = " AND ".join(f"{{{k}}}" for k in sanitized)
    else:
        # Default fuzzy mode: double quotes
        terms_str = " AND ".join(f'"{k}"' for k in sanitized)

    query = f"TITLE-ABS-KEY({terms_str})"

    # Validate
    if query.count("(") != query.count(")"):
        raise ValueError("Balanced parentheses validation failed for Scopus query.")
    if not query.startswith("TITLE-ABS-KEY("):
        raise ValueError("Invalid Scopus query prefix.")

    return query


def build_flat_query(keywords: list) -> str:
    """Format a space-separated string of the first 10 keywords."""
    sanitized = [sanitize_term(k) for k in keywords if sanitize_term(k)]
    # Use only first 10 terms
    truncated = sanitized[:10]
    return " ".join(truncated)


def generate_all(summary_id: int, keywords_list: list, exact_scopus: bool = False, force: bool = False) -> dict:
    """Generate, validate, and store search queries for the 5 databases."""
    db_logger.init_db()

    # Generate queries
    wos_q = build_wos_query(keywords_list)
    scopus_q = build_scopus_query(keywords_list, exact=exact_scopus)
    flat_q = build_flat_query(keywords_list)

    targets = {
        "WOS": wos_q,
        "Scopus": scopus_q,
        "SemanticScholar": flat_q,
        "OpenAlex": flat_q,
        "CrossRef": flat_q,
    }

    results = {
        "_meta": {
            "summary_id": summary_id,
            "keywords_extracted": keywords_list,
            "exact_scopus": exact_scopus,
            "force": force
        }
    }

    for db_name, query_string in targets.items():
        if not query_string:
            results[db_name] = {"error": "Empty query generated"}
            continue

        try:
            # Check duplicate
            is_dup = db_logger.check_duplicate(summary_id, db_name)
            if is_dup and not force:
                results[db_name] = {
                    "query": query_string,
                    "skipped": True,
                    "reason": "duplicate"
                }
            else:
                new_id = db_logger.store_query(summary_id, db_name, query_string)
                results[db_name] = {
                    "query": query_string,
                    "stored_id": new_id
                }
        except Exception as e:
            results[db_name] = {
                "query": query_string,
                "error": str(e)
            }

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and store academic database queries.")
    parser.add_argument("summary_id", type=int, help="The target summaries.id to link the queries to.")
    parser.add_argument("--keywords", type=str, required=True, help="Comma-separated keywords to build queries with.")
    parser.add_argument("--exact-scopus", action="store_true", help="Use Scopus exact-phrase curly braces.")
    parser.add_argument("--force", action="store_true", help="Bypass deduplication checks and force insert.")

    args = parser.parse_args()

    # Parse comma separated keywords
    kw_raw = args.keywords.split(",")
    kws = [sanitize_term(k) for k in kw_raw if sanitize_term(k)]

    if not kws:
        print(json.dumps({"error": "No valid keywords provided."}))
        sys.exit(1)

    output = generate_all(args.summary_id, kws, exact_scopus=args.exact_scopus, force=args.force)
    print(json.dumps(output, indent=2))
