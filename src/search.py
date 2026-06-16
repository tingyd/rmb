import sqlite3


def search_exact(conn: sqlite3.Connection, query: str) -> list[dict]:
    """Return rows where body or tags LIKE %query%."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, body, tags, created FROM notes WHERE body LIKE ? or tags LIKE ?",
        (f"%{query}%", f"%{query}%"),
    )
    rows = cursor.fetchall()
    return [{"id": r[0], "body": r[1], "tags": r[2], "created": r[3]} for r in rows]


def search_fuzzy(
    conn: sqlite3.Connection, query: str, threshold: float = 0.6
) -> list[dict]:
    """
    Fetch all notes, compute fuzzy similarity for each,
    return those above threshold sorted by score descending.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, body, tags, created FROM notes")

    result = []
    rows = cursor.fetchall()

    for r in rows:
        score = similarity(query, r[1])
        if score > threshold:
            result.append(
                {
                    "id": r[0],
                    "body": r[1],
                    "tags": r[2],
                    "created": r[3],
                    "score": score,
                }
            )

    return sorted(result, key=lambda x: x["score"], reverse=True)


def similarity(a, b) -> float:
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    overlap = len(a_tokens & b_tokens)
    longer = max(len(a_tokens), len(b_tokens))
    return overlap / longer
