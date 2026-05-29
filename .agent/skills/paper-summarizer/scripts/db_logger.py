import sys
import os
import sqlite3
import hashlib
import json

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "research.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    
    valid = False
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
            has_papers = cursor.fetchone() is not None
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='summaries'")
            has_summaries = cursor.fetchone() is not None
            conn.close()
            if has_papers and has_summaries:
                valid = True
        except Exception:
            pass
            
    if not valid:
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        example_path = os.path.join(".agent", "skills", "paper-summarizer", "assets", "example.db")
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, DB_PATH)
            
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create papers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        file_name TEXT NOT NULL,
        file_hash TEXT UNIQUE,
        first_analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create summaries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        summary_file_path TEXT NOT NULL,
        summary_file_hash TEXT NOT NULL,
        title TEXT,
        authors TEXT,
        publication_year INTEGER,
        motivation TEXT,
        methodology TEXT,
        evaluation_data TEXT,
        limitations TEXT,
        summary_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def compute_sha256(file_path):
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_hash(file_path):
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File '{file_path}' not found", "exists": False}))
        return
    
    file_hash = compute_sha256(file_path)
    file_name = os.path.basename(file_path)
    
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check by hash
    cursor.execute("SELECT id, file_path, first_analyzed_at FROM papers WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()
    
    if row:
        paper_id, db_file_path, first_analyzed_at = row
        # Fetch the latest summary title and id if exists
        cursor.execute("SELECT id, title, summary_file_path FROM summaries WHERE paper_id = ? ORDER BY id DESC LIMIT 1", (paper_id,))
        sum_row = cursor.fetchone()
        summary_id = sum_row[0] if sum_row else None
        title = sum_row[1] if sum_row else None
        sum_path = sum_row[2] if sum_row else None
        
        summary_file_exists = False
        if sum_path and os.path.exists(sum_path):
            summary_file_exists = True
        
        result = {
            "exists": True,
            "match_by": "hash",
            "paper_id": paper_id,
            "summary_id": summary_id,
            "db_file_path": db_file_path,
            "file_name": file_name,
            "file_hash": file_hash,
            "title": title,
            "summary_file_path": sum_path,
            "summary_file_exists": summary_file_exists,
            "first_analyzed_at": first_analyzed_at
        }
    else:
        # Check by path (in case content changed but path is same)
        cursor.execute("SELECT id, file_hash, first_analyzed_at FROM papers WHERE file_path = ?", (file_path,))
        row_path = cursor.fetchone()
        if row_path:
            paper_id, db_file_hash, first_analyzed_at = row_path
            # Fetch the latest summary title and id if exists
            cursor.execute("SELECT id, title, summary_file_path FROM summaries WHERE paper_id = ? ORDER BY id DESC LIMIT 1", (paper_id,))
            sum_row = cursor.fetchone()
            summary_id = sum_row[0] if sum_row else None
            title = sum_row[1] if sum_row else None
            sum_path = sum_row[2] if sum_row else None
            
            summary_file_exists = False
            if sum_path and os.path.exists(sum_path):
                summary_file_exists = True
                
            result = {
                "exists": True,
                "match_by": "path",
                "paper_id": paper_id,
                "summary_id": summary_id,
                "db_file_path": file_path,
                "file_name": file_name,
                "file_hash": file_hash,
                "db_file_hash": db_file_hash,
                "title": title,
                "summary_file_path": sum_path,
                "summary_file_exists": summary_file_exists,
                "first_analyzed_at": first_analyzed_at
            }
        else:
            result = {
                "exists": False,
                "file_hash": file_hash,
                "file_name": file_name
            }
            
    conn.close()
    print(json.dumps(result))

def log_summary(paper_path, summary_path, metadata_json_str):
    if not os.path.exists(paper_path):
        print(json.dumps({"success": False, "error": f"Paper file '{paper_path}' not found"}))
        return
    
    init_db()
    file_hash = compute_sha256(paper_path)
    file_name = os.path.basename(paper_path)
    
    # Read summary content
    if not os.path.exists(summary_path):
        print(json.dumps({"success": False, "error": f"Summary file '{summary_path}' not found"}))
        return
    with open(summary_path, "r", encoding="utf-8") as f:
        summary_content = f.read()
    summary_hash = hashlib.sha256(summary_content.encode("utf-8")).hexdigest()
    
    try:
        meta = json.loads(metadata_json_str)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Invalid metadata JSON: {str(e)}"}))
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if paper already exists (by hash first, then by path)
        cursor.execute("SELECT id FROM papers WHERE file_hash = ?", (file_hash,))
        row = cursor.fetchone()
        
        if row:
            paper_id = row[0]
            # Update path if it changed
            cursor.execute("UPDATE papers SET file_path = ? WHERE id = ?", (paper_path, paper_id))
        else:
            cursor.execute("SELECT id FROM papers WHERE file_path = ?", (paper_path,))
            row_path = cursor.fetchone()
            if row_path:
                paper_id = row_path[0]
                # Update hash (content changed)
                cursor.execute("UPDATE papers SET file_hash = ? WHERE id = ?", (file_hash, paper_id))
            else:
                # Insert new paper
                cursor.execute(
                    "INSERT INTO papers (file_path, file_name, file_hash) VALUES (?, ?, ?)",
                    (paper_path, file_name, file_hash)
                )
                paper_id = cursor.lastrowid
        
        # Coerce publication_year to integer or None
        pub_year = meta.get("publication_year")
        if pub_year is not None:
            try:
                # Remove any non-digit chars or try direct conversion
                pub_year = int(str(pub_year).strip())
            except ValueError:
                pub_year = None
                
        # Insert summary record
        cursor.execute(
            """
            INSERT INTO summaries (
                paper_id, summary_file_path, summary_file_hash, title, authors, 
                publication_year, motivation, methodology, evaluation_data, limitations, summary_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id, summary_path, summary_hash,
                meta.get("title"), meta.get("authors"), pub_year,
                meta.get("motivation"), meta.get("methodology"), meta.get("evaluation_data"),
                meta.get("limitations"), summary_content
            )
        )
        conn.commit()
        result = {"success": True, "paper_id": paper_id, "summary_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        result = {"success": False, "error": str(e)}
        
    conn.close()
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_logger.py [init | check-hash <file_path> | log <paper_path> <summary_path> <metadata_json>]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "init":
        init_db()
        print(json.dumps({"success": True}))
    elif cmd == "check-hash":
        if len(sys.argv) < 3:
            print("Error: check-hash command requires file_path argument")
            sys.exit(1)
        check_hash(sys.argv[2])
    elif cmd == "log":
        if len(sys.argv) < 5:
            print("Error: log command requires paper_path, summary_path, and metadata_json arguments")
            sys.exit(1)
        log_summary(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Error: Unknown command '{cmd}'")
        sys.exit(1)
