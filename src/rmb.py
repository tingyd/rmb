import argparse, os, sys
from datetime import datetime
from colorama import init, Fore, Style

from db import (
    add_note,
    delete_by_id,
    export_notes,
    filter_by_tag,
    get_note_by_id,
    init_db,
    list_notes,
)
from search import search_exact
from tui import SearchApp

init(autoreset=True)


def print_help():
    print(
        "\nrmb commands:\n"
        '  add "<note>" [#tag1 #tag2]  save a note\n'
        "  search <query>              search notes by body or tag\n"
        "  list [--limit N]            show recent notes (default 20)\n"
        "  tag <tag>                   filter notes by tag\n"
        "  delete <id>                 delete a note by ID\n"
        "  tui                         live search interface\n"
        "  help                        show this message \n"
    )


def format_note_md(note):
    date = datetime.strptime(note["created"], "%Y-%m-%d %H:%M:%S")
    lines = [f"## [{note['id']}] {date.strftime('%b %d, %Y')}"]
    lines.append(note["body"])
    if note["tags"]:
        lines.append(note["tags"])
    lines.append("\n---")
    return "\n".join(lines)


def format_note(note):
    date = datetime.strptime(note["created"], "%Y-%m-%d %H:%M:%S")
    date_str = Fore.CYAN + date.strftime("%m/%d/%y") + Style.RESET_ALL
    body = note["body"]
    lines = [date_str, f"  {body}"]
    if note["tags"]:
        lines.append(Fore.YELLOW + f"  {note['tags']}" + Style.RESET_ALL)
    lines.append(Style.DIM + "-" * 40 + Style.RESET_ALL)
    return "\n".join(lines)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")
COMMANDS = {"add", "search", "tag", "delete", "help", "export", "tui", "list"}
if len(sys.argv) > 1 and sys.argv[1] not in COMMANDS:
    print_help()
    sys.exit(0)

for cmd in ("add", "search", "tag", "delete", "help", "export", "tui"):
    subparsers.add_parser(cmd).add_argument("args", nargs="*")

list_parser = subparsers.add_parser("list")
list_parser.add_argument("--limit", type=int, default=20)


parsed = parser.parse_args()
if parsed.command is None:
    print('usage: rmb add "<note>" [#tag1 #tag2]', file=sys.stderr)
    sys.exit(1)

body = ""
tags = []


try:
    conn = init_db(os.path.expanduser("~/.rmb/notes.db"))

    if hasattr(parsed, "args"):
        for arg in parsed.args:
            if arg.startswith("#"):
                tags.append(arg)
            else:
                body = arg

    match parsed.command:
        case "help":
            print_help()
        case "add":
            add_note(conn, body, tags)
        case "search":
            for note in search_exact(conn, body):
                print(format_note(note))
        case "list":
            for note in list_notes(conn, parsed.limit):
                print(format_note(note))
        case "tag":
            for note in filter_by_tag(conn, body):
                print(format_note(note))
        case "delete":
            id = int(body)
            note = get_note_by_id(conn, id)
            if note is not None:
                confirm = input(f'Delete note {id}: "{note[0]}"? [y/N] ')
                if confirm.lower() == "y":
                    delete_by_id(conn, id)
            else:
                print(f"error: note {id} not found", file=sys.stderr)
                sys.exit(1)
        case "export":
            for note in export_notes(conn):
                print(format_note_md(note))
        case "tui":
            SearchApp().run()
        case _:
            print_help()

    conn.close()
except Exception as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
