from textual.app import ComposeResult
from textual.widgets import Footer
from textual.containers import Container, Horizontal

from .base_screen import BaseScreen
from ..widgets.userInputArea import UserInputArea
from ..widgets.markdownArea import MasterMarkdown


class EditorScreen(BaseScreen):
    """Editor Only — UserInput + Preview, no transcription."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-row"):
            yield UserInputArea(show_line_numbers=True, id="user")
            with Container(id="right-column"):
                yield MasterMarkdown(id="master")

        with Horizontal(id="bottom-bar"):
            yield Footer()
