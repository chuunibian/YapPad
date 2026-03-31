from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label
from textual.binding import Binding

from pathlib import Path


class NewFileOverlay(ModalScreen[Path | None]):
    """Overlay for creating a new file in the selected directory."""

    BINDINGS = [
        Binding("ctrl+n", "create_file", "Create", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, target_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self._target_dir = target_dir

    def compose(self) -> ComposeResult:
        # show which folder the file will be created in
        relative = self._target_dir.name or str(self._target_dir)
        with Vertical(id="new-file-body"):
            yield Label("New Note", id="new-file-title")
            yield Label(f"📁 {relative}/", id="new-file-location")
            yield Input(placeholder="Filename (e.g. my-notes.md)", id="new-file-name")
        yield Footer()

    def action_create_file(self) -> None:
        name_input = self.query_one("#new-file-name", Input)
        filename = name_input.value.strip()

        if not filename:
            self.notify("Filename cannot be empty", severity="error")
            return

        # ensure .md extension if not provided
        if not filename.endswith(".md"):
            filename += ".md"

        self._target_dir.mkdir(parents=True, exist_ok=True)
        target_file = self._target_dir / filename

        if target_file.exists():
            self.notify(f"File already exists: {filename}", severity="warning")
            return

        target_file.write_text("", encoding="utf-8")
        self.dismiss(target_file)

    def action_cancel(self) -> None:
        self.dismiss(None)
