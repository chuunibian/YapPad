from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label


class CustomTranscriptFooter(Horizontal):

    queue_count: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Label("Queue: —", id="queue-indicator")

    def watch_queue_count(self, count: int) -> None:
        indicator = self.query_one("#queue-indicator", Label)
        if count == 0:
            indicator.update("Queue: —")
        else:
            squares = "".join("[green]■[/green]" for _ in range(count))
            indicator.update(f"Queue: {squares}")
