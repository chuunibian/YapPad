from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label
from textual.binding import Binding


from pathlib import Path


class NewFileOverlay(ModalScreen[Path | None]):
    """Overlay for creating a new file in the app data directory."""

    BINDINGS = [
        Binding("ctrl+n", "create_file", "Create", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="new-file-body"):
            yield Label("New Note", id="new-file-title")
            yield Input(placeholder="Filename (e.g. my-notes.md)", id="new-file-name")
            yield Input(
                placeholder="Subdirectory (optional, e.g. lectures)", id="new-file-path"
            )
        yield Footer()

    def action_create_file(self) -> None:
        name_input = self.query_one("#new-file-name", Input)
        path_input = self.query_one("#new-file-path", Input)

        filename = name_input.value.strip()
        subdir = path_input.value.strip()

        if not filename:
            self.notify("Filename cannot be empty", severity="error")
            return

        # ensure .md extension if not provided
        if not filename.endswith(".md"):
            filename += ".md"

        data_dir = Path(self.app.config.document_dir)
        target_dir = data_dir / subdir if subdir else data_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / filename

        if target_file.exists():
            self.notify(f"File already exists: {filename}", severity="warning")
            return

        target_file.write_text("", encoding="utf-8")
        self.dismiss(target_file)

    def action_cancel(self) -> None:
        self.dismiss(None)
