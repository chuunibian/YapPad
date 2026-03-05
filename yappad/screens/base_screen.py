from textual.app import ComposeResult
from textual.widgets import Footer, TextArea
from textual.containers import Horizontal
from textual import on, work
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive
from textual.worker import get_current_worker

from ..widgets.userInputArea import UserInputArea
from ..widgets.markdownArea import MasterMarkdown
from ..widgets.popupComponent import PopupComponent

from pathlib import Path


class BaseScreen(Screen):
    """
    Base screen with shared logic for file management, save/load, popup, and commit.
    All layout screens extend this.
    """

    BINDINGS = [
        Binding("alt+y", "temp_commit", "commit", priority=True, show=False),
        Binding("ctrl+o", "open_popup", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
    ]

    CSS_PATH = "../styles/temp2.tcss"

    # reactive states
    current_file_path: reactive[str] = reactive("")
    is_saved: reactive[bool] = reactive(True)

    # --------------------------------------- On X -------------------------------------------------

    @on(TextArea.Changed, '#user')
    def on_user_input_changed(self) -> None:
        if self.current_file_path:
            self.is_saved = False

    # --------------------------------------- Actions -------------------------------------------------

    def action_temp_commit(self) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        master_markdown_widget = self.query_one("#master", MasterMarkdown)

        if user_input_widget.text != "":
            master_markdown_widget.update(user_input_widget.text)
            user_input_widget.text = ""
        else:
            self.notify("Nothing in user input area to append")

    def action_open_popup(self) -> None:
        self.app.push_screen(PopupComponent(), callback=self._on_file_selected)

    def _on_file_selected(self, path) -> None:
        if path is not None:
            self.load_file(path)

    def _apply_loaded_file(self, file_path: str, content: str) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        user_input_widget.text = content
        self.current_file_path = file_path
        self.is_saved = True

    # reactive callback
    def watch_current_file_path(self, new_path: str) -> None:
        self._update_border_title()

    def watch_is_saved(self, saved: bool) -> None:
        self._update_border_title()

    def _update_border_title(self) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        if self.current_file_path:
            name = Path(self.current_file_path).name
            prefix = "● " if not self.is_saved else ""
            user_input_widget.border_title = f"{prefix}{name}"
        else:
            user_input_widget.border_title = "Input"

    def action_save_file(self) -> None:
        if not self.current_file_path:
            self.notify("No file open to save", severity="warning")
            return
        user_input_widget = self.query_one("#user", TextArea)
        self._save_file_to_disk(self.current_file_path, user_input_widget.text)

    def _on_save_complete(self) -> None:
        self.is_saved = True
        self.notify("Saved")

    # --------------------------------------- Workers -------------------------------------------------

    @work(thread=True)
    def _save_file_to_disk(self, file_path: str, content: str) -> None:
        worker = get_current_worker()
        try:
            Path(file_path).write_text(content, encoding="utf-8")
            if not worker.is_cancelled:
                self.app.call_from_thread(self._on_save_complete)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self.notify, f"Failed to save: {e}", severity="error")

    @work(thread=True)
    def load_file(self, path: Path) -> None:
        worker = get_current_worker()
        try:
            content = path.read_text(encoding="utf-8")
            if not worker.is_cancelled:
                self.app.call_from_thread(self._apply_loaded_file, str(path), content)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self.notify, f"Failed to load: {e}", severity="error")
