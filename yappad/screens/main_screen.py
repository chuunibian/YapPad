from textual.app import ComposeResult
from textual.widgets import Footer
from textual.containers import Container, Horizontal
from textual.binding import Binding

from .base_screen import BaseScreen
from ..widgets.userInputArea import UserInputArea
from ..widgets.markdownArea import MasterMarkdown
from ..widgets.transcriptTabs import TranscriptTabs
from ..widgets.quickActionOverlay import QuickAction, JumpTarget
from ..core.models import TranscriptClip


class MainScreen(BaseScreen):
    """Main App View — UserInput + Preview + Mic & Loopback tabs."""

    BINDINGS = BaseScreen.BINDINGS + [
        Binding("alt+s", "toggle_record", "record toggle", priority=True),
        Binding("alt+d", "toggle_loopback_record", "loopback toggle", priority=True),
        Binding("alt+m", "grab_mic_transcript", "grab mic", priority=True),
        Binding("alt+l", "grab_loopback_transcript", "grab loopback", priority=True),
        Binding("alt+j", "mic_tab_prev", "mic tab ←", priority=True),
        Binding("alt+k", "mic_tab_next", "mic tab →", priority=True),
        Binding("alt+h", "loopback_tab_prev", "lb tab ←", priority=True),
        Binding("alt+n", "loopback_tab_next", "lb tab →", priority=True),
    ]

    # --------------------------------------- Compose -------------------------------------------------

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-row"):
            yield UserInputArea(show_line_numbers=True, id="user")
            with Container(id="right-column"):
                yield MasterMarkdown(id="master")
                with Horizontal(id="transcript-row"):
                    yield TranscriptTabs(label="Mic", id="mic-tabs")
                    yield TranscriptTabs(label="Loopback", id="loopback-tabs")

        with Horizontal(id="bottom-bar"):
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#master", MasterMarkdown).display = False
        self._sync_right_column()

    def _get_jump_targets(self):
        targets = super()._get_jump_targets()
        targets.extend(
            [
                JumpTarget(
                    "t",
                    "Mic Transcript",
                    "mic-tabs",
                    actions=[
                        QuickAction("r", "Rec", "toggle_record"),
                        QuickAction("m", "Grab", "grab_mic_transcript"),
                    ],
                ),
                JumpTarget(
                    "b",
                    "Loopback Transcript",
                    "loopback-tabs",
                    actions=[
                        QuickAction("d", "Rec", "toggle_loopback_record"),
                        QuickAction("k", "Grab", "grab_loopback_transcript"),
                    ],
                ),
            ]
        )
        return targets

    # --------------------------------------- Recording -------------------------------------------------

    def action_toggle_record(self) -> None:
        app = self.app
        app.is_recording = not app.is_recording

        if app.is_recording:
            if app.mic_engine.get_recording_status() == False:
                app.mic_engine.start_recording()
        else:
            if app.mic_engine.get_recording_status() == True:
                temp_audio = app.mic_engine.stop_recording()
                app.audio_queue_mic.put(temp_audio)

        self._update_recording_indicator()

    def action_toggle_loopback_record(self) -> None:
        app = self.app
        app.is_loopback_recording = not app.is_loopback_recording

        if app.is_loopback_recording:
            if app.loopback_engine.get_recording_status() == False:
                app.loopback_engine.start_recording()
        else:
            if app.loopback_engine.get_recording_status() == True:
                temp_audio = app.loopback_engine.stop_recording()
                app.audio_queue_loopback.put(temp_audio)

        self._update_recording_indicator()

    # --------------------------------------- Transcript -------------------------------------------------

    def action_grab_mic_transcript(self) -> None:
        tabs = self.query_one("#mic-tabs", TranscriptTabs)
        text = tabs.grab_active()
        if text:
            self.app.copy_to_clipboard(text)
        else:
            self.notify("Nothing to grab!")

    def action_grab_loopback_transcript(self) -> None:
        tabs = self.query_one("#loopback-tabs", TranscriptTabs)
        text = tabs.grab_active()
        if text:
            self.app.copy_to_clipboard(text)
        else:
            self.notify("Nothing to grab!")

    # ---- Tab cycling ----

    def action_mic_tab_prev(self) -> None:
        self.query_one("#mic-tabs", TranscriptTabs).prev_tab()

    def action_mic_tab_next(self) -> None:
        self.query_one("#mic-tabs", TranscriptTabs).next_tab()

    def action_loopback_tab_prev(self) -> None:
        self.query_one("#loopback-tabs", TranscriptTabs).prev_tab()

    def action_loopback_tab_next(self) -> None:
        self.query_one("#loopback-tabs", TranscriptTabs).next_tab()

    # callbacks
    def append_transcript_mic(self, clip: TranscriptClip):
        tabs = self.query_one("#mic-tabs", TranscriptTabs)
        tabs.add_clip(clip)

    def append_transcript_loopback(self, clip: TranscriptClip):
        tabs = self.query_one("#loopback-tabs", TranscriptTabs)
        tabs.add_clip(clip)
