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
from ..widgets.settingsOverlay import SettingsOverlay
from ..widgets.quickActionOverlay import QuickActionOverlay, QuickAction, JumpTarget
from ..core.messages import FileDeleted

from pathlib import Path


class BaseScreen(Screen):
    """
    Base screen with shared logic for file management, save/load, popup, and commit.
    All layout screens extend this.
    """

    BINDINGS = [
        Binding("alt+y", "temp_commit", "commit", priority=True, show=False),
        Binding("ctrl+o", "open_popup", "Open"),
        Binding("ctrl+l", "open_settings", "Settings"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+u", "quick_actions", "Quick Actions", priority=True),
    ]

    CSS_PATH = "../styles/temp2.tcss"

    # reactive states
    current_file_path: reactive[str] = reactive("")
    is_saved: reactive[bool] = reactive(True)

    # --------------------------------------- On X -------------------------------------------------

    @on(TextArea.Changed, "#user")
    def on_user_input_changed(self) -> None:
        if self.current_file_path:
            self.is_saved = False

    # --------------------------------------- Actions -------------------------------------------------

    def action_temp_commit(self) -> None:
        """
        For now this will commit the current text in the notes to the preview
        keybind should be visible anywhere

        """
        user_input_widget = self.query_one("#user", TextArea)
        master_markdown_widget = self.query_one("#master", MasterMarkdown)

        if user_input_widget.text != "":
            master_markdown_widget.update(user_input_widget.text)
        else:
            self.notify("Nothing in user input area to append")

    def on_file_deleted(self, message: FileDeleted) -> None:
        """If the deleted file is currently open, clear the editor."""
        if (
            self.current_file_path
            and Path(self.current_file_path).resolve() == message.path.resolve()
        ):
            user_input_widget = self.query_one("#user", TextArea)
            user_input_widget.text = ""
            self.current_file_path = ""
            self.is_saved = True
            self.notify("Open file was deleted", severity="warning")

    def action_open_popup(self) -> None:
        self.app.push_screen(PopupComponent(), callback=self._on_file_selected)

    def action_open_settings(self) -> None:
        self.app.push_screen(SettingsOverlay())

    def _on_file_selected(self, path) -> None:
        if path is not None:
            self.load_file(path)

    # --------------------------------------- Quick Actions -------------------------------------------------

    def _get_jump_targets(self) -> list[JumpTarget]:
        """Return the list of panels that can be jumped to.
        Each panel can carry associated action keybinds.
        Subclasses extend this to add screen-specific panels."""
        return [
            JumpTarget(
                "i",
                "Input",
                "user",
                actions=[
                    QuickAction("o", "Open", "open_popup"),
                    QuickAction("s", "Save", "save_file"),
                ],
            ),
            JumpTarget(
                "p",
                "Preview",
                "master",
                actions=[
                    QuickAction("y", "Commit", "temp_commit"),
                ],
            ),
        ]

    def _get_quick_actions(self) -> list[QuickAction]:
        """Return the list of global actions (not attached to a panel).
        Subclasses extend this to add screen-specific actions."""
        return [
            QuickAction("1", "Editor", "mode:editor"),
            QuickAction("2", "Mic", "mode:mic"),
            QuickAction("3", "Loopback", "mode:loopback"),
            QuickAction("4", "Full", "mode:full"),
        ]

    def action_quick_actions(self) -> None:
        """Open the quick-action / jump overlay."""
        jump_targets = self._get_jump_targets()
        actions = self._get_quick_actions()
        self.app.push_screen(
            QuickActionOverlay(jump_targets, actions),
            callback=self._on_quick_action_selected,
        )

    def _on_quick_action_selected(self, result: tuple[str, str] | None) -> None:
        """Dispatch the selected quick action or jump target."""
        if result is None:
            return

        kind, value = result
        if kind == "jump":
            # focus the target widget
            try:
                widget = self.query_one(f"#{value}")
                widget.focus()
            except Exception:
                pass
        elif kind == "action":
            if value.startswith("mode:"):
                mode = value.split(":", 1)[1]
                self.app.switch_mode(mode)
            else:
                method = getattr(self, f"action_{value}", None)
                if method:
                    method()

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
                self.app.call_from_thread(
                    self.notify, f"Failed to save: {e}", severity="error"
                )

    @work(thread=True)
    def load_file(self, path: Path) -> None:
        worker = get_current_worker()
        try:
            content = path.read_text(encoding="utf-8")
            if not worker.is_cancelled:
                self.app.call_from_thread(self._apply_loaded_file, str(path), content)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify, f"Failed to load: {e}", severity="error"
                )
