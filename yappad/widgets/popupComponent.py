from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer
from textual.binding import Binding

from .localFileExplorer import LocalFileExplorer
from .localSettings import LocalSettings
from .newFileOverlay import NewFileOverlay
from .deleteConfirmOverlay import DeleteConfirmOverlay
from pathlib import Path
from ..core.messages import FileSelected, FileDeleted


class PopupComponent(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss_popup", "Close", show=False),
        Binding("ctrl+o", "dismiss_popup", "Close"),
        Binding("ctrl+q", "quit", "Quit App"),
        Binding("ctrl+n", "new_file", "New Note"),
        Binding("delete", "delete_selected", "Delete", show=True),
        Binding("ctrl+d", "delete_selected", "Delete", show=False),
    ]

    def compose(self) -> ComposeResult:
        data_dir = Path(self.app.config.document_dir)
        with Horizontal(id="popup-body"):
            with Vertical(id="popup-left"):
                yield LocalFileExplorer(str(data_dir), id="file-tree")
            with Vertical(id="popup-right"):
                yield LocalSettings(id="settings-panel")
        yield Footer()

    def on_file_selected(self, message: FileSelected) -> None:
        """When a file is selected in the explorer, dismiss with the path."""
        self.dismiss(message.path)

    # using same keybind pop it off the app go back to the note screen
    def action_dismiss_popup(self) -> None:
        self.dismiss(None)

    # since modal screen catches events the normal ctrl+q quit keybind needs active catching
    def action_quit(self) -> None:
        self.app.exit()

    def action_new_file(self) -> None:
        """Open the new file overlay."""
        self.app.push_screen(NewFileOverlay(), callback=self._on_new_file_created)

    def _on_new_file_created(self, path) -> None:
        """Called when the new file overlay dismisses."""
        if path is not None:
            # refresh the file tree so the new file shows up
            file_tree = self.query_one("#file-tree", LocalFileExplorer)
            file_tree.reload()
            self.notify(f"Created: {path.name}")

    def action_delete_selected(self) -> None:
        """Delete the currently highlighted file or folder after confirmation."""
        file_tree = self.query_one("#file-tree", LocalFileExplorer)
        target = file_tree.get_selected_path()

        if target is None:
            self.notify("Nothing selected to delete", severity="warning")
            return

        # don't allow deleting the root document directory
        data_dir = Path(self.app.config.document_dir).resolve()
        if target.resolve() == data_dir:
            self.notify("Cannot delete the root documents folder", severity="error")
            return

        # capture the target path for the callback closure
        deleted_path = target
        self.app.push_screen(
            DeleteConfirmOverlay(target),
            callback=lambda result: self._on_delete_confirmed(result, deleted_path),
        )

    def _on_delete_confirmed(self, result, deleted_path: Path) -> None:
        """Called when the delete overlay dismisses."""
        if result is True:
            file_tree = self.query_one("#file-tree", LocalFileExplorer)
            file_tree.reload()
            self.notify(f"Deleted: {deleted_path.name}")
            # post FileDeleted so the screen can react if the open file was removed
            self.post_message(FileDeleted(deleted_path))

