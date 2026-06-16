import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from textual.app import App, ComposeResult
from textual.widgets import Input, ListView, ListItem, Label

from db import init_db, list_notes
from search import search_exact


class SearchApp(App):
    CSS = """
    Input {
        margin: 1 2;
    }
    ListView {
        margin: 0 2;
    }
    .note-body {
        color: $text;
    }
    .note-meta {
        color: $text-muted;
    }
    """
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Input(placeholder="search notes...")
        yield ListView()

    def on_mount(self) -> None:
        self.conn = init_db(os.path.expanduser("~/.rmb/notes.db"))
        self._refresh_results("")

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_results(event.value)

    def _refresh_results(self, query: str) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        notes = search_exact(self.conn, query) if query else list_notes(self.conn, 5)
        for note in notes:
            date = note["created"][:10]
            date_str = f"[cyan]{date}[/cyan]"
            tags = f" [yellow] {note['tags']}[/yellow]" if note["tags"] else ""
            lv.append(
                ListItem(Label(f"[{note['id']}] {date_str}  {note['body']}{tags}"))
            )

    def on_unmount(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    SearchApp().run()
