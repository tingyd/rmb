import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import add_note, delete_by_id, filter_by_tag, list_notes
from search import search_exact, search_fuzzy


def _init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            body    TEXT NOT NULL,
            tags    TEXT,
            created TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    _init_schema(conn)
    yield conn
    conn.close()


def test_add_note(db):
    row_id = add_note(db, "JWT tokens don't store state server-side", [])
    row = db.execute("SELECT body FROM notes WHERE id = ?", (row_id,)).fetchone()
    assert row is not None
    assert row[0] == "JWT tokens don't store state server-side"


def test_add_note_with_tags(db):
    row_id = add_note(db, "use consistent hashing", ["#distributed", "#systems"])
    row = db.execute("SELECT tags FROM notes WHERE id = ?", (row_id,)).fetchone()
    assert "#distributed" in row[0]
    assert "#systems" in row[0]


def test_search_exact_matches(db):
    add_note(db, "Levenshtein distance measures edit distance between strings", [])
    add_note(db, "binary search runs in O(log n)", [])
    results = search_exact(db, "Levenshtein")
    assert len(results) == 1
    assert "Levenshtein" in results[0]["body"]


def test_search_exact_no_match(db):
    add_note(db, "binary search runs in O(log n)", [])
    results = search_exact(db, "quicksort")
    assert results == []


def test_search_exact_matches_tags(db):
    add_note(db, "some note", ["#rust"])
    results = search_exact(db, "rust")
    assert len(results) == 1


def test_search_fuzzy_finds_close_match(db):
    add_note(db, "async await in JavaScript", [])
    results = search_fuzzy(db, "async await", threshold=0.3)
    assert len(results) >= 1
    assert any("async" in r["body"] for r in results)


def test_search_empty_db(db):
    results = search_exact(db, "anything")
    assert results == []


def test_search_fuzzy_empty_db(db):
    results = search_fuzzy(db, "anything")
    assert results == []


def test_list_notes_default_limit(db):
    for i in range(25):
        add_note(db, f"note {i}", [])
    results = list_notes(db)
    assert len(results) == 20


def test_list_notes_custom_limit(db):
    for i in range(10):
        add_note(db, f"note {i}", [])
    results = list_notes(db, limit=5)
    assert len(results) == 5


def test_list_notes_empty_db(db):
    results = list_notes(db)
    assert results == []


def test_filter_by_tag(db):
    add_note(db, "note about rust", ["#rust"])
    add_note(db, "note about python", ["#python"])
    add_note(db, "note about both", ["#rust", "#python"])
    results = filter_by_tag(db, "rust")
    assert len(results) == 2
    assert all("#rust" in r["tags"] for r in results)


def test_filter_by_tag_no_match(db):
    add_note(db, "note about python", ["#python"])
    results = filter_by_tag(db, "rust")
    assert results == []


def test_filter_by_tag_without_hash(db):
    add_note(db, "note about rust", ["#rust"])
    results = filter_by_tag(db, "rust")
    assert len(results) == 1



def test_delete(db):
    row_id = add_note(db, "delete this note", [])
    result = delete_by_id(db, row_id)
    assert result == 1
    assert db.execute("SELECT id FROM notes WHERE id = ?", (row_id,)).fetchone() is None


def test_delete_not_found(db):
    result = delete_by_id(db, 9999)
    assert result == 0
