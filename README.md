# rmb

A minimal command-line tool for saving and searching your own notes - without leaving the terminal.

## Purpose

This project is primarily a learning exercise - to understand how CLI tools work, how SQLite stores data, and how fuzzy search is implemented under the hood.

The tool itself is useful if you live in the terminal. Stickies or a notepad work fine for most people, but `rmb` has one advantage: search. When you've saved hundreds of notes over months, `rmb search "JWT"` beats scrolling through a sticky pile. Every note lives in one place, searchable instantly, no app to open.

```bash
rmb add "JWT tokens don't store state server-side - all info is in the token itself"
rmb add "use consistent hashing when you need to add/remove nodes without reshuffling everything"
rmb add "Levenshtein distance = min edits to turn one string into another"
```

Later:

```bash
rmb search "JWT"
rmb search "hashing"
rmb list
```

## Usage

```
rmb add "<note>"           save a note
rmb search "<query>"       search your notes (exact + fuzzy)
rmb list [--limit N]       show N most recent notes (default 20)
rmb tag <tag>              filter notes by tag
rmb delete <id>            delete a note by ID (asks for confirmation)
rmb export                 print all notes as markdown (pipe to file: rmb export > notes.md)
rmb tui                    live search interface
rmb help                   show available commands
```

## Stack

- Python
- SQLite (local, no server, no internet)

## Status

v1.0 - feature complete.
