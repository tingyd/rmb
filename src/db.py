import sqlite3
import os


def init_db(db_path: str) -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure schema exists."""

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes(
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            body    TEXT NOT NULL,
            tags    TEXT,
            created TEXT DEFAULT (datetime('now'))
        );
        """)
    conn.commit()
    return conn


def add_note(conn: sqlite3.Connection, body: str, tags: list[str]) -> int:
    """Insert a note; return its new row id."""
    tag_string = ",".join(tags) if tags else ""

    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes(body, tags) VALUES (?, ?)", (body, tag_string))
    conn.commit()
    return cursor.lastrowid


def list_notes(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Return the N most recent notes, sorted newest first."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, body, tags, created FROM notes
                   ORDER BY created DESC
                   LIMIT ?
                   """,
        (limit,),
    )

    rows = cursor.fetchall()
    return [{"id": r[0], "body": r[1], "tags": r[2], "created": r[3]} for r in rows]


def filter_by_tag(conn: sqlite3.Connection, tag: str) -> list[dict]:
    """Return all notes that have the given tag."""
    cursor = conn.cursor()
    tag = tag.lstrip("#")
    cursor.execute(
        """
        SELECT id, body, tags, created FROM notes
            WHERE tags like ?
                   """,
        (f"%#{tag}%",),
    )

    rows = cursor.fetchall()
    return [{"id": r[0], "body": r[1], "tags": r[2], "created": r[3]} for r in rows]


def delete_by_id(conn: sqlite3.Connection, id: int) -> int:
    """Return number of rows being delete"""
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM notes
        where id = ?""",
        (id,),
    )
    conn.commit()
    return cursor.rowcount


def get_note_by_id(conn: sqlite3.Connection, id: int) -> int:
    """Return the note found by ID, None if not found"""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT body FROM notes
        where id = ?""",
        (id,),
    )
    return cursor.fetchone()


def export_notes(conn: sqlite3.Connection) -> list[dict]:
    """Return all the notes sorted newest first."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, body, tags, created FROM notes
                   ORDER BY created DESC
                   """,
    )

    rows = cursor.fetchall()
    return [{"id": r[0], "body": r[1], "tags": r[2], "created": r[3]} for r in rows]
