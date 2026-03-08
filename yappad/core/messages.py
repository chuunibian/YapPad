# for custom messages sent by components
from textual.message import Message
from pathlib import Path


class FileSelected(Message):
    """Posted when the user selects a file in the explorer."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
