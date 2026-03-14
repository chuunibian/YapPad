import shutil

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label
from textual.binding import Binding

from pathlib import Path


class DeleteConfirmOverlay(ModalScreen[bool | None]):
    """Confirmation overlay before deleting a file or directory."""

    BINDINGS = [
        Binding("enter", "confirm_delete", "Confirm Delete", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, target_path: Path) -> None:
        super().__init__()
        self.target_path = target_path

    def compose(self) -> ComposeResult:
        is_dir = self.target_path.is_dir()
        kind = "folder" if is_dir else "file"

        with Vertical(id="delete-confirm-body"):
            yield Label("Confirm Delete", id="delete-confirm-title")
            yield Label(
                f"Delete {kind}: [bold]{self.target_path.name}[/bold]",
                id="delete-confirm-target",
            )
            if is_dir:
                yield Label(
                    "⚠ This will remove the folder and ALL its contents.",
                    id="delete-confirm-warning",
                )
            yield Label(
                "Press [bold]Enter[/bold] to confirm or [bold]Escape[/bold] to cancel.",
                id="delete-confirm-hint",
            )
        yield Footer()

    def action_confirm_delete(self) -> None:
        try:
            if self.target_path.is_dir():
                shutil.rmtree(self.target_path)
            else:
                self.target_path.unlink()
            self.dismiss(True)
        except Exception as e:
            self.notify(f"Failed to delete: {e}", severity="error")
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
