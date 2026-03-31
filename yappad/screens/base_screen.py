from textual.widgets import TextArea
from textual.containers import Container
from textual import on, work
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive
from textual.worker import get_current_worker

from ..widgets.markdownArea import MasterMarkdown
from ..widgets.popupComponent import PopupComponent
from ..widgets.settingsOverlay import SettingsOverlay
from ..widgets.quickActionOverlay import QuickActionOverlay, QuickAction, JumpTarget
from ..core.messages import FileDeleted
from ..core.storage import save_config

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
        Toggle preview: if hidden, commit text, hide editor, and show preview.
        If visible, hide preview and show editor again.
        """
        master = self.query_one("#master", MasterMarkdown)
        user_input_widget = self.query_one("#user", TextArea)

        if not master.display:
            # hide editor, show preview
            if user_input_widget.text != "":
                 master.document.update(user_input_widget.text)
            user_input_widget.display = False
            master.display = True
        else:
            # show editor, hide preview
            master.display = False
            user_input_widget.display = True
            user_input_widget.focus()

        self._sync_right_column()

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

    def _sync_right_column(self) -> None:
        """
        Show or hide the right column based on what is visible inside it.
        When preview is active, transcript row is always hidden so preview is fullscreen.
        """
        try:
            right_column = self.query_one("#right-column", Container)
            master_preview = self.query_one("#master", MasterMarkdown)
        except Exception:
            return

        is_preview_active = master_preview.display

        try:
            transcript_row = self.query_one("#transcript-row")
            mic_tabs = self.query_one("#mic-tabs")
            loopback_tabs = self.query_one("#loopback-tabs")

            # hide transcript row if preview is active, otherwise show based on tab content
            if is_preview_active:
                transcript_row.display = False
            elif mic_tabs.display or loopback_tabs.display:
                transcript_row.display = True
            else:
                transcript_row.display = False

            is_transcript_row_visible = transcript_row.display
        except Exception:
            is_transcript_row_visible = False

        # right column visible if EITHER preview OR transcript row is visible
        if is_preview_active or is_transcript_row_visible:
            right_column.display = True
        else:
            right_column.display = False

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
        return []

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
            # invoke the action method
            action_method = getattr(self, f"action_{value}", None)
            if action_method:
                action_method()
            else:
                self.notify(f"Unknown action: {value}", severity="warning")

    def _apply_loaded_file(self, file_path: str, content: str) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        user_input_widget.text = content
        self.current_file_path = file_path
        self.is_saved = True

        # persist last opened file path so --resume can restore it
        self.app.config.last_opened_file = file_path
        save_config(self.app.config)

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

    def _update_recording_indicator(self) -> None:
        """Update the border subtitle on the input widget to show recording status."""
        user_input_widget = self.query_one("#user", TextArea)
        parts = []
        if getattr(self.app, "is_recording", False):
            parts.append("🔴 Mic")
        if getattr(self.app, "is_loopback_recording", False):
            parts.append("🔴 Loopback")
        if parts:
            user_input_widget.border_subtitle = " | ".join(parts)
        else:
            user_input_widget.border_subtitle = "⚪"

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
