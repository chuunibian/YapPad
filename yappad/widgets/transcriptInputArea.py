from textual.widgets import TextArea


class TranscriptRichLog(TextArea):
    BORDER_TITLE = "Transcript"

    def on_mount(self) -> None:
        # self.border_subtitle = "Transcript Q: 0"
        pass
