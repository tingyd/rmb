# rmb

**Read the entire doc before you start.**

## Introduction

In this project you will build a command-line tool called `rmb` that lets you capture
thoughts, tag them, and retrieve them instantly via fuzzy search.
The goal is to deeply understand how data persistence works in a CLI tool, how SQLite
operates under the hood, and how fuzzy matching algorithms work.

```
rmb add "async/await in Rust is different from JS" #rust #learning
rmb search rust
```

Notes live in a local SQLite database - no internet required, always available.

> Build incrementally. Get `rmb add` working first, then search, then polish.

---

## Background: How SQLite Works

SQLite is a serverless, embedded relational database. Unlike PostgreSQL or MySQL,
there is no separate server process — the entire database is a single file on disk
(usually `~/.rmb/notes.db`).

When you call `sqlite3.connect("notes.db")`, SQLite opens (or creates) that file.
All reads and writes go through the SQLite library directly.

### SQLite Page Format (high level)

Internally, a `.db` file is divided into fixed-size *pages* (default 4096 bytes).
The first page is the "database header" — it contains metadata like page size,
schema version, and encoding. After that come *table b-tree pages* that store rows.

You don't need to know this to use SQLite, but it explains why:
- SQLite is fast for read-heavy workloads (single file, no network)
- Concurrent writes are handled with file-level locking
- The `.db` file is portable across platforms

### SQL Refresher

```sql
-- Create the notes table
CREATE TABLE IF NOT EXISTS notes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    body      TEXT NOT NULL,
    tags      TEXT,          -- comma-separated, e.g. "#rust,#learning"
    created   TEXT DEFAULT (datetime('now'))
);

-- Insert a note
INSERT INTO notes (body, tags) VALUES ('async/await in Rust is different from JS', '#rust,#learning');

-- Full-text query (basic LIKE)
SELECT id, body, tags, created FROM notes WHERE body LIKE '%rust%' OR tags LIKE '%rust%';
```

---

## Background: Fuzzy Matching

Exact string matching (`LIKE '%rust%'`) requires the query to appear literally.
Fuzzy matching finds strings that are *close* to the query even if not exact.

### Levenshtein Distance

The most common fuzzy metric. The *edit distance* between two strings is the minimum
number of single-character edits (insertions, deletions, substitutions) to transform
one string into the other.

```
edit("rust", "ruts") = 2   (swap 's' and 't')
edit("rust", "Rust") = 1   (capitalization)
edit("rust", "rusting") = 3
```

For search you typically compute similarity as:
```
similarity = 1 - (edit_distance / max(len(a), len(b)))
```
A threshold of 0.6 is a reasonable starting point.

### Token-based Fuzzy Matching

An alternative: tokenize both the query and candidate into words, then check if
any query token partially matches any candidate token. This is simpler to implement
and works well for short notes.

The `fuzzywuzzy` Python library (or its successor `thefuzz`) wraps Levenshtein distance
and provides helpers like `fuzz.partial_ratio` and `fuzz.token_sort_ratio`.

---

## Project Structure

```
rmb/
├── src/
│   ├── rmb.py      # Entry point + CLI subcommand dispatch
│   ├── db.py       # All database logic
│   ├── search.py   # Fuzzy search logic
│   └── tui.py      # TUI live search
├── tests/
│   └── test_rmb.py
├── SPEC.md
└── README.md
```

---

## Part 1: `rmb add` — Storing Notes

Your first task is to implement:

```
rmb add "<text>" [#tag1 #tag2 ...]
```

**Spec:**
- Parse the command-line. The note body is the first non-tag argument.
  Tags are any argument starting with `#`.
- Store the note in SQLite at `~/.rmb/notes.db`.
- Print nothing on success (follow Unix conventions — silence means success).
- Print a one-line error to stderr and exit non-zero on any failure.

**Schema:** (create on first run if table doesn't exist)

```sql
CREATE TABLE IF NOT EXISTS notes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    body    TEXT NOT NULL,
    tags    TEXT,
    created TEXT DEFAULT (datetime('now'))
);
```

**Functions to implement in `db.py`:**

```python
def init_db(db_path: str) -> sqlite3.Connection

def add_note(conn: sqlite3.Connection, body: str, tags: list[str]) -> int
```

`tags` is stored as a comma-joined string, e.g. `"#rust,#learning"`.

---

## Part 2: `rmb search` — Retrieving Notes

```
rmb search <query>
```

**Spec:**
- Accept one or more query terms.
- Search both the `body` and `tags` columns.
- Print each matching note as:
  ```
  [id] [created]  body  [tags]
  ```
- If no results, print nothing and exit 0.

**Implement in two phases:**

**Phase 1 - Exact (LIKE):**

```python
def search_exact(conn: sqlite3.Connection, query: str) -> list[dict]
```

Returns rows where body or tags `LIKE %query%`. Each dict has keys `id`, `body`,
`tags`, `created`.

**Phase 2 - Fuzzy:**

```python
def search_fuzzy(conn: sqlite3.Connection, query: str, threshold: float = 0.6) -> list[dict]
```

Fetch all notes from SQLite, score each one against `query` using `thefuzz`, and
return matches above `threshold` sorted by score descending.

For fuzzy, load all notes from SQLite and score them in Python. This is fine for
thousands of notes. If you had millions, you'd pre-build an inverted index.

---

## Part 3: `rmb list` — Show Recent Notes

```
rmb list [--limit N]
```

- Print the N most recent notes (default 20).
- Format: one note per line, sorted newest first.

---

## Part 4: `rmb tag` — Filter by Tag

```
rmb tag rust
```

- Return all notes that have `#rust` in their tags column (exact match on the tag token).

**Implementation note:** storing tags as a comma-separated string works for a simple
tool. If you wanted to query tags efficiently at scale, you'd have a separate `tags`
table with a foreign key to `notes`. For this project, the simple approach is fine.

---

## Part 5: `rmb delete` - Remove a Note

```
rmb delete 42
```

- Delete the note with the given ID.
- Prompt for confirmation before deleting - show the note body first so you know
  what you're about to lose:

```
$ rmb delete 42
Delete note 42: "async/await in Rust is different from JS"? [y/N]
```

- If the ID doesn't exist, print an error and exit non-zero (don't fail silently).

**Implementation notes:**
- `input()` for the confirmation prompt; treat anything other than `y`/`Y` as no.
- `DELETE FROM notes WHERE id = ?` - then check `cursor.rowcount` to detect
  whether anything was actually deleted (0 means the ID didn't exist).
- IDs are `AUTOINCREMENT`, so a deleted ID is never reused - gaps in `rmb list`
  output are normal and fine.

---

## Part 6: TUI Live Search

Use `textual` (Python) or `bubbletea` (Go) to build a live search window:

- Input box at the top.
- As you type, results update in real time below.
- Arrow keys navigate, Enter copies the note body to clipboard.

This is genuinely fun to build and teaches you about event-driven UI loops.

---

## Part 7 (Stretch): Browser Extension

A companion browser extension that:
1. Lets you highlight text on any webpage and right-click -> "Save to rmb"
2. POSTs `{ text, url, title }` to a local HTTP server (you'll add a `rmb serve` command)
3. The local server calls `add_note()` with the text and source URL as a tag

This teaches you browser extension APIs and local HTTP communication.

---

## Part 8: `rmb export`

```
rmb export > notes.md
```

- Dump all notes as markdown to stdout, newest first - one section per note with
  its ID, date, tags, and body.
- Because it writes to stdout, the user chooses the destination with `>` - this is
  the Unix way (and exactly what pipes-and-redirection fluency is for).
- Insurance against lock-in: your notes are never trapped in the database.

---

## Implementation Notes

- Use `argparse` (stdlib) for CLI parsing and subcommands. It handles `add`, `search`,
  `list`, and `tag` subcommands cleanly with `add_subparsers`.
- Use `sqlite3` (stdlib) for all database access. No third-party driver needed.
- The database file path should default to `~/.rmb/notes.db`.
  Use `os.path.expanduser("~")` to resolve the home directory, then `os.path.join`
  to build the full path.
- Create the `~/.rmb/` directory if it doesn't exist before opening the database:
  ```python
  os.makedirs(os.path.dirname(db_path), exist_ok=True)
  ```
- Always close the connection when done, or use it as a context manager:
  ```python
  with sqlite3.connect(db_path) as conn:
      ...
  ```
- Install `thefuzz` for fuzzy matching:
  ```
  pip install thefuzz[speedup]
  ```
  The `[speedup]` extra installs `python-Levenshtein` for faster string comparison.

---

## Testing

Write tests in `tests/test_rmb.py` using `unittest` or `pytest`.

Use an **in-memory SQLite database** for all tests so you never touch the real
`~/.rmb/notes.db`:

```python
import sqlite3
from db import init_db, add_note
from search import search_exact, search_fuzzy

def new_test_conn():
    conn = sqlite3.connect(":memory:")
    init_db_schema(conn)  # or however you expose schema creation
    return conn
```

Tests to write:
- `test_add_note`: insert a note, query the DB directly, verify the row exists.
- `test_search_exact`: insert two notes, search for a term that only matches one.
- `test_search_fuzzy`: insert a note with "async/await", search for "async await" (no slash).
- `test_tag_filter`: insert notes with different tags, verify tag filter returns only the right ones.
- `test_empty_search`: search when DB is empty — should return empty list, not error.
- `test_delete`: insert a note, delete it by ID, verify the row is gone. Also try deleting a nonexistent ID — should report failure, not crash.

Run tests:
```bash
pytest tests/
```

Run with verbose output to see individual test names:
```bash
pytest -v tests/
```

---

## Engineering Standards

Follow these throughout - the point is building production habits, not just the tool:

**Git**
- Branch per feature: `feature/add-command`, `feature/delete-command`
- Descriptive commit messages: `Add fuzzy search to rmb search command`, not `fix stuff`
- No committing directly to `main`

**Code quality**
- Functions do one thing
- Every function has a docstring
- No magic numbers or hardcoded strings - use constants
- Handle errors explicitly, never silently swallow exceptions

**Documentation**
- Keep `README.md` up to date as commands land
- Non-obvious logic gets a comment explaining *why*, not *what*

---

## What You'll Learn

By finishing this project you'll understand:
- How SQLite stores data and why it's so fast for local tools
- How to design a minimal but useful CLI interface
- The tradeoffs between exact and fuzzy string matching
- Why Unix tools are silent on success and verbose on failure
- How to write tests for a tool that depends on a database

---

## Definition of Done

The core tool (Parts 1-5) is shipped when:
- You can add a note in under 3 seconds from your terminal
- You can find any note you've ever saved in under 5 seconds
- Every command has at least one test, and `pytest tests/` passes
- Another developer could read the codebase and understand it without you explaining

Out of scope for v1: GUI, cloud sync, multi-user anything. It's a local tool - keep it that way until the core is solid.
