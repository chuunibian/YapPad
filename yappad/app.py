from .screens.main_screen import MarkdownLogScreen
from .screens.viewer_screen import MarkdownViewerScreen
from .storage import get_data_dir

from textual.app import App, ComposeResult
from textual.command import Provider, Hit
from textual.theme import Theme

class ModeSwitchProvider(Provider):
    """Injects mode-switching commands into the Command Palette."""
    async def search(self, query: str):
        matcher = self.matcher(query)
        
        targets = [
            ("main", "Switch to YapPad"),
            ("markdown", "Switch to Markdown Viewer"),
        ]
        
        for mode, description in targets:
            if matcher.match(description):
                yield Hit(
                    score=1.0,
                    match_display=matcher.highlight(description),
                    command=lambda m=mode: self.app.switch_mode(m),
                    help=f"Change active mode to {mode}"
                )

class YapPad(App):

    MODES = {
        "main": MarkdownLogScreen,
        "markdown": MarkdownViewerScreen,
    }

    COMMANDS = App.COMMANDS | {ModeSwitchProvider}

    def on_mount(self) -> None:

        # ensure app data directory exists on startup
        get_data_dir()

        default_theme = Theme(
            name="default",
            primary="#C45AFF",
            secondary="#a684e8",
            warning="#FFD700",
            error="#FF4500",
            success="#00FA9A",
            accent="#FF69B4",
            background="#0F0F1F",
            surface="#1E1E3F",
            panel="#2D2B55",
            dark=True,
            variables={
                "footer-background": "transparent",
            },
        )

        self.register_theme(default_theme)
        self.theme = "default"

        self.switch_mode("main")

if __name__ == "__main__":
    app = YapPad()
    app.run()

