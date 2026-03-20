from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer
from textual.binding import Binding

from .localSettings import LocalSettings

class SettingsOverlay(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss_popup", "Close", show=False),
        Binding("ctrl+l", "dismiss_popup", "Close"),
        Binding("ctrl+q", "quit", "Quit App"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield LocalSettings(id="settings-panel")
        yield Footer()

    def action_dismiss_popup(self) -> None:
        self.dismiss(None)

    def action_quit(self) -> None:
        self.app.exit()
