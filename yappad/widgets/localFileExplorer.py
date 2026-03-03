from textual.widgets import DirectoryTree
from pathlib import Path
from typing import Iterable
from ..messages import FileSelected


class LocalFileExplorer(DirectoryTree):
    """File explorer rooted at the app data directory."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if not path.name.startswith(".")]

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Bubble up a FileSelected message when a file is clicked.

        would want the parent root to catch to then load the file and write to the user input area
        
        
        """

        self.post_message(FileSelected(event.path))