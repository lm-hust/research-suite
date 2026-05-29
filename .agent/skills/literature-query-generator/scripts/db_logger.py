"""
db_logger.py — literature-query-generator

Manages the `queries` table in data/research.db.
"""
import sys
import os
import sqlite3
import json
import shutil

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "research.db")
SEED_DB_PATH = os.path.join(".agent", "skills", "paper-summarizer", "assets", "example.db")


def init_db():
    """Ensure data/research.db exists and contains the `queries` table.

    If the DB is absent or lacks queries table, delete the existing one and copy
    the paper-summarizer example.db, then create the queries table.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    has_queries_table = False
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='queries'")
            exists = cursor.fetchone() is not None
            if exists:
                # Also check if it's the old schema containing md_file_path
                cursor.execute("PRAGMA table_info(queries)")
                cols = [col[1] for col in cursor.fetchall()]
                if "md_file_path" not in cols:
                    has_queries_table = True
            conn.close()
        except Exception:
            pass

    if not has_queries_table:
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        if os.path.exists(SEED_DB_PATH):
            shutil.copy(SEED_DB_PATH, DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        summary_id   INTEGER NOT NULL,
        database     TEXT NOT NULL,
        query_string TEXT NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (summary_id) REFERENCES summaries (id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()


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
            "SELECT id FROM summaries WHERE summary_file_path = ? ORDER BY id DESC LIMIT 1",
            (candidate,)
        )
        row = cursor.fetchone()
        if row:
            summary_id = row[0]
            break

    conn.close()
    return summary_id


def check_duplicate(summary_id: int, database: str) -> bool:
    """Return True if a query already exists for this summary + database combo."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM queries WHERE summary_id = ? AND database = ? LIMIT 1",
        (summary_id, database)
    )
    exists = cursor.fetchone() is not None

    conn.close()
    return exists


def store_query(summary_id: int, database: str, query_string: str) -> int:
    """Insert a new row into the queries table and return its id."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO queries (summary_id, database, query_string)
        VALUES (?, ?, ?)
        """,
        (summary_id, database, query_string)
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
        rows = [dict(r) for r in cursor.fetchall()]
    else:
        rows = []

    conn.close()
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_logger.py [init | store <summary_id> <database> <query_string> | get <md_path>]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_db()
        print(json.dumps({"success": True}))

    elif cmd == "store":
        if len(sys.argv) < 5:
            print("Error: store requires: summary_id database query_string")
            sys.exit(1)
        sid = int(sys.argv[2])
        db_name = sys.argv[3]
        qs = sys.argv[4]
        new_id = store_query(sid, db_name, qs)
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
