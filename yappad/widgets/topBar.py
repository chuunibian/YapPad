from textual.containers import Horizontal
from textual.widgets import Input, Label
from textual.app import ComposeResult


class TopBar(Horizontal):

    def compose(self) -> ComposeResult:
        # yield Label("Search: ", id="top-bar-icon")
        yield Input(placeholder="Search or type a command...", id="top-bar-input")
