from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label
from textual.binding import Binding

from pathlib import Path


class NewFolderOverlay(ModalScreen[Path | None]):
    """Overlay for creating a new folder in the selected directory."""

    BINDINGS = [
        Binding("ctrl+f", "create_folder", "Create", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, target_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self._target_dir = target_dir

    def compose(self) -> ComposeResult:
        relative = self._target_dir.name or str(self._target_dir)
        with Vertical(id="new-folder-body"):
            yield Label("New Folder", id="new-folder-title")
            yield Label(f"📁 {relative}/", id="new-folder-location")
            yield Input(placeholder="Folder name (e.g. lectures)", id="new-folder-name")
        yield Footer()

    def action_create_folder(self) -> None:
        name_input = self.query_one("#new-folder-name", Input)
        folder_name = name_input.value.strip()

        if not folder_name:
            self.notify("Folder name cannot be empty", severity="error")
            return

        target = self._target_dir / folder_name

        if target.exists():
            self.notify(f"Already exists: {folder_name}", severity="warning")
            return

        target.mkdir(parents=True, exist_ok=True)
        self.dismiss(target)

    def action_cancel(self) -> None:
        self.dismiss(None)
