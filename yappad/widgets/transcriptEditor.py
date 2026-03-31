from textual.app import ComposeResult
from textual.containers import Vertical
from .transcriptInputArea import TranscriptRichLog
from .customTranscriptFooter import CustomTranscriptFooter


class TranscriptEditor(Vertical):
    # to create it via caller set css id
    def __init__(self, transcript_id: str = "transcript", **kwargs):
        super().__init__(**kwargs)
        self._transcript_id = transcript_id

    def compose(self) -> ComposeResult:
        yield TranscriptRichLog(show_line_numbers=True, id=self._transcript_id)
        yield CustomTranscriptFooter()
