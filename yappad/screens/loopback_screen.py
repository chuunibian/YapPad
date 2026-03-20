from textual.app import ComposeResult
from textual.widgets import Footer, TextArea
from textual.containers import Container, Horizontal
from textual.binding import Binding

from .base_screen import BaseScreen
from ..widgets.userInputArea import UserInputArea
from ..widgets.markdownArea import MasterMarkdown
from ..widgets.transcriptEditor import TranscriptEditor
from ..widgets.customTranscriptFooter import CustomTranscriptFooter
from ..widgets.quickActionOverlay import QuickAction, JumpTarget

import numpy as np


class LoopbackScreen(BaseScreen):
    """Loopback Mode — UserInput + Preview + Loopback transcript."""

    BINDINGS = BaseScreen.BINDINGS + [
        Binding("alt+d", "toggle_loopback_record", "loopback toggle", priority=True),
        Binding("alt+l", "grab_loopback_transcript", "grab loopback", priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-row"):
            yield UserInputArea(show_line_numbers=True, id="user")
            with Container(id="right-column"):
                yield MasterMarkdown(id="master")
                yield TranscriptEditor(
                    transcript_id="transcript-loopback", id="transcript-editor-loopback"
                )

        with Horizontal(id="bottom-bar"):
            yield Footer()

    def on_mount(self) -> None:
        self.query_one(
            "#transcript-loopback", TextArea
        ).border_title = "⚪ Loopback Idle"

    def _get_jump_targets(self):
        targets = super()._get_jump_targets()
        targets.append(
            JumpTarget(
                "t",
                "Loopback",
                "transcript-loopback",
                actions=[
                    QuickAction("r", "Rec", "toggle_loopback_record"),
                    QuickAction("k", "Grab", "grab_loopback_transcript"),
                ],
            )
        )
        return targets

    # --------------------------------------- Recording -------------------------------------------------

    def action_toggle_loopback_record(self) -> None:
        app = self.app
        app.is_loopback_recording = not app.is_loopback_recording
        loopback_widget = self.query_one("#transcript-loopback", TextArea)

        if app.is_loopback_recording:
            loopback_widget.border_title = "🔴 Loopback Recording"
            if app.loopback_engine.get_recording_status() == False:
                app.loopback_engine.start_recording()
        else:
            loopback_widget.border_title = "⚪ Loopback Idle"
            if app.loopback_engine.get_recording_status() == True:
                temp_audio = app.loopback_engine.stop_recording()
                app.audio_queue_loopback.put(temp_audio)

    # --------------------------------------- Transcript -------------------------------------------------

    def action_grab_loopback_transcript(self) -> None:
        self._grab_transcript(
            "transcript-loopback",
            "transcript-editor-loopback",
            self.app.transcript_queue_loopback,
        )

    def _grab_transcript(
        self, widget_id: str, editor_id: str, queue_list: list
    ) -> None:
        transcript_widget = self.query_one(f"#{widget_id}", TextArea)

        if len(queue_list) != 0:
            current_data = transcript_widget.text
            self.app.copy_to_clipboard(current_data)

            next_data = queue_list.pop(0)
            footer = self.query_one(
                f"#{editor_id} CustomTranscriptFooter", CustomTranscriptFooter
            )
            footer.queue_count = len(queue_list)
            transcript_widget.text = next_data

        elif transcript_widget.text != "":
            current_data = transcript_widget.text
            self.app.copy_to_clipboard(current_data)
            transcript_widget.text = ""
        else:
            self.notify("Nothing to grab in transcript box!")

    def append_transcript_loopback(self, transcribed_text):
        transcript_widget = self.query_one(f"#transcript-loopback", TextArea)
        if transcript_widget.text == "":
            transcript_widget.text = transcribed_text
        else:
            self.app.transcript_queue_loopback.append(transcribed_text)
            footer = self.query_one(
                f"#transcript-editor-loopback CustomTranscriptFooter",
                CustomTranscriptFooter,
            )
            footer.queue_count = len(self.app.transcript_queue_loopback)
