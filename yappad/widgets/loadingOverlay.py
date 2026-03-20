from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator


class LoadingOverlay(ModalScreen[None]):
    """Blocking modal that shows a loading indicator while a model is switching.

    Cannot be dismissed by the user — only programmatically via call_from_thread
    after the worker finishes.
    """

    def __init__(self, message: str = "Loading model...") -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="loading-body"):
            yield Label(self._message, id="loading-message")
            yield LoadingIndicator()
