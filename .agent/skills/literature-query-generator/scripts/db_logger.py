"""
db_logger.py — literature-query-generator

Manages the `queries` table in data/research.db.
Does NOT modify the existing `papers` or `summaries` tables.

Usage:
    python db_logger.py init
    python db_logger.py store <summary_id|""> <md_file_path|""> <database> <query_string>
    python db_logger.py get <md_file_path>
"""
import sys
import os
import sqlite3
import json
import shutil

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "research.db")
ASSETS_EXAMPLE_DB = os.path.join(
    os.path.dirname(__file__), "..", "assets", "example.db"
)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Ensure data/research.db exists and contains the `queries` table.

    If the DB is absent, copy assets/example.db as a seed (which contains
    papers + summaries + queries), then apply CREATE TABLE IF NOT EXISTS so
    this function is safe to run on both fresh and existing databases.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        example = os.path.abspath(ASSETS_EXAMPLE_DB)
        if os.path.exists(example):
            shutil.copy(example, DB_PATH)
        # If example DB also missing just create a new blank file

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Add queries table only — never touch papers/summaries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        summary_id   INTEGER,
        md_file_path TEXT,
        database     TEXT NOT NULL,
        query_string TEXT NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (summary_id) REFERENCES summaries (id) ON DELETE SET NULL
    )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_path_candidates(md_file_path: str) -> list:
    """Return all slash-normalized versions of the input path candidate."""
    if not md_file_path:
        return []
    raw = [
        md_file_path,
        os.path.normpath(md_file_path),
    ]
    try:
        raw.append(os.path.abspath(md_file_path))
        raw.append(os.path.relpath(md_file_path))
    except Exception:
        pass

    candidates = []
    for r in raw:
        candidates.append(r)
        candidates.append(r.replace('\\', '/'))
        candidates.append(r.replace('/', '\\'))

    return list(dict.fromkeys(candidates))


def resolve_summary_id(md_file_path: str):
    """Return the summaries.id whose summary_file_path matches md_file_path.

    Tries both the raw path and its absolute/relative normalisation.
    Returns None if no match is found.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    candidates = _get_path_candidates(md_file_path)

    summary_id = None
    for candidate in candidates:
        cursor.execute(
            "SELECT id FROM summaries WHERE summary_file_path = ?",
            (candidate,)
        )
        row = cursor.fetchone()
        if row:
            summary_id = row[0]
            break

    conn.close()
    return summary_id


def check_duplicate(summary_id, md_file_path: str, database: str) -> bool:
    """Return True if a query already exists for this source + database combo.

    Uses summary_id when available (nullable FK), otherwise falls back to
    md_file_path matching.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if summary_id is not None:
        cursor.execute(
            "SELECT 1 FROM queries WHERE summary_id = ? AND database = ? LIMIT 1",
            (summary_id, database)
        )
        exists = cursor.fetchone() is not None
    else:
        candidates = _get_path_candidates(md_file_path)
        exists = False
        for candidate in candidates:
            cursor.execute(
                """SELECT 1 FROM queries
                   WHERE summary_id IS NULL
                   AND database = ?
                   AND md_file_path = ?
                   LIMIT 1""",
                (database, candidate)
            )
            if cursor.fetchone():
                exists = True
                break

    conn.close()
    return exists


def store_query(summary_id, md_file_path: str, database: str, query_string: str) -> int:
    """Insert a new row into the queries table and return its id."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Store md_file_path as normalised relative path when possible
    try:
        rel_path = os.path.normpath(os.path.relpath(md_file_path)) if md_file_path else None
    except ValueError:
        rel_path = os.path.normpath(md_file_path)  # different drives on Windows

    cursor.execute(
        """
        INSERT INTO queries (summary_id, md_file_path, database, query_string)
        VALUES (?, ?, ?, ?)
        """,
        (summary_id, rel_path, database, query_string)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_queries_for_md(md_file_path: str) -> list:
    """Return all query rows for a given MD source as a list of dicts."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    summary_id = resolve_summary_id(md_file_path)

    if summary_id is not None:
        cursor.execute(
            "SELECT * FROM queries WHERE summary_id = ? ORDER BY created_at DESC",
            (summary_id,)
        )
    else:
        candidates = _get_path_candidates(md_file_path)
        rows = []
        seen_ids = set()
        for candidate in candidates:
            cursor.execute(
                "SELECT * FROM queries WHERE summary_id IS NULL AND md_file_path = ? ORDER BY created_at DESC",
                (candidate,)
            )
            for r in cursor.fetchall():
                if r["id"] not in seen_ids:
                    rows.append(dict(r))
                    seen_ids.add(r["id"])
        conn.close()
        return rows

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_logger.py [init | store <summary_id|-> <md_file_path|-> <database> <query_string> | get <md_path>]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_db()
        print(json.dumps({"success": True}))

    elif cmd == "store":
        if len(sys.argv) < 6:
            print("Error: store requires: summary_id|- md_file_path|- database query_string")
            sys.exit(1)
        raw_sid = sys.argv[2]
        md_path = sys.argv[3] if sys.argv[3] != "-" else None
        db_name = sys.argv[4]
        qs = sys.argv[5]
        sid = int(raw_sid) if raw_sid not in ("-", "") else None
        new_id = store_query(sid, md_path or "", db_name, qs)
        print(json.dumps({"success": True, "query_id": new_id}))

    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Error: get requires md_file_path")
            sys.exit(1)
        rows = get_queries_for_md(sys.argv[2])
        print(json.dumps(rows, default=str))

    else:
        print(f"Error: Unknown command '{cmd}'")
        sys.exit(1)
