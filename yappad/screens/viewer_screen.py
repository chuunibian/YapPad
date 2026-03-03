from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DirectoryTree, Markdown, Header, Footer

class MarkdownViewerScreen(Screen):
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DirectoryTree("C:/Windows/WinSxS", id="file-tree")
            yield Markdown("# Select a Markdown file from the left", id="md-viewer")
        yield Footer()

