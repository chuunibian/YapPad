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


class MicScreen(BaseScreen):
    """Mic Mode — UserInput + Preview + Mic transcript."""

    BINDINGS = BaseScreen.BINDINGS + [
        Binding("alt+s", "toggle_record", "record toggle", priority=True),
        Binding("alt+m", "grab_mic_transcript", "grab mic", priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-row"):
            yield UserInputArea(show_line_numbers=True, id="user")
            with Container(id="right-column"):
                yield MasterMarkdown(id="master")
                yield TranscriptEditor(id="transcript-editor")

        with Horizontal(id="bottom-bar"):
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#transcript", TextArea).border_title = "⚪ Mic Idle"

    def _get_jump_targets(self):
        targets = super()._get_jump_targets()
        targets.append(
            JumpTarget(
                "t",
                "Transcript",
                "transcript",
                actions=[
                    QuickAction("r", "Rec", "toggle_record"),
                    QuickAction("m", "Grab", "grab_mic_transcript"),
                ],
            )
        )
        return targets

    # --------------------------------------- Recording -------------------------------------------------

    def action_toggle_record(self) -> None:
        app = self.app
        app.is_recording = not app.is_recording
        mic_widget = self.query_one("#transcript", TextArea)

        if app.is_recording:
            mic_widget.border_title = "🔴 Mic Recording"
            if app.mic_engine.get_recording_status() == False:
                app.mic_engine.start_recording()
        else:
            mic_widget.border_title = "⚪ Mic Idle"
            if app.mic_engine.get_recording_status() == True:
                temp_audio = app.mic_engine.stop_recording()
                app.audio_queue_mic.put(temp_audio)

    # --------------------------------------- Transcript -------------------------------------------------

    def action_grab_mic_transcript(self) -> None:
        self._grab_transcript(
            "transcript", "transcript-editor", self.app.transcript_queue_mic
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

    def append_transcript_mic(self, transcribed_text):
        transcript_widget = self.query_one(f"#transcript", TextArea)
        if transcript_widget.text == "":
            transcript_widget.text = transcribed_text
        else:
            self.app.transcript_queue_mic.append(transcribed_text)
            footer = self.query_one(
                f"#transcript-editor CustomTranscriptFooter", CustomTranscriptFooter
            )
            footer.queue_count = len(self.app.transcript_queue_mic)
