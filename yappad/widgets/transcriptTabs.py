from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import TabbedContent, TabPane, Static

from uuid import uuid4


class TranscriptTabs(Vertical):
    """Tabbed transcript viewer. Each tab = one TranscriptClip.

    Hidden when empty, visible when clips exist.
    Uses TabbedContent.add_pane / remove_pane to stay in sync.
    """

    DEFAULT_CSS = """
    TranscriptTabs {
        border: round #444444;
        border-title-color: #a684e8;
        background: transparent;
    }
    """

    def __init__(self, label: str = "Transcript", **kwargs):
        super().__init__(**kwargs)
        self._clips: list = []  # list[TranscriptClip] kept in sync with pane order
        self._pane_ids: list[str] = []  # parallel list of pane IDs
        self._label = label

    def compose(self) -> ComposeResult:
        yield TabbedContent()

    def on_mount(self) -> None:
        self.border_title = self._label
        # start hidden
        self.display = False

    # ── public API ──

    def add_clip(self, clip) -> None:
        """Append a new transcript clip as a tab."""
        pane_id = f"clip-{uuid4().hex[:8]}"
        self._clips.append(clip)
        self._pane_ids.append(pane_id)

        pane = TabPane(clip.timestamp, Static(clip.text, classes="clip-text"), id=pane_id)
        tabbed = self.query_one(TabbedContent)
        tabbed.add_pane(pane)

        # show the widget now that we have content
        # set self to display true and let app sync to sync it
        self.display = True
        if hasattr(self.screen, "_sync_right_column"):
            self.screen._sync_right_column()

    def grab_active(self) -> str | None:
        """Return the active tab's text, remove it, and hide if empty."""
        if len(self._clips) == 0:
            return None

        tabbed = self.query_one(TabbedContent)
        active_pane = tabbed.active_pane
        if active_pane is None:
            return None

        # find index by pane id
        pane_id = active_pane.id
        if pane_id in self._pane_ids:
            idx = self._pane_ids.index(pane_id)
            clip = self._clips.pop(idx)
            self._pane_ids.pop(idx)
            text = clip.text
        else:
            # fallback: read text from the Static widget
            text = str(active_pane.query_one(".clip-text", Static).renderable)

        tabbed.remove_pane(pane_id)

        # hide if no more clips
        if len(self._clips) == 0:
            self.display = False
            if hasattr(self.screen, "_sync_right_column"):
                self.screen._sync_right_column()

        return text

    def next_tab(self) -> None:
        """Switch to the next transcript tab."""
        if len(self._pane_ids) < 2:
            return
        tabbed = self.query_one(TabbedContent)
        current = tabbed.active
        if current in self._pane_ids:
            idx = (self._pane_ids.index(current) + 1) % len(self._pane_ids)
            tabbed.active = self._pane_ids[idx]

    def prev_tab(self) -> None:
        """Switch to the previous transcript tab."""
        if len(self._pane_ids) < 2:
            return
        tabbed = self.query_one(TabbedContent)
        current = tabbed.active
        if current in self._pane_ids:
            idx = (self._pane_ids.index(current) - 1) % len(self._pane_ids)
            tabbed.active = self._pane_ids[idx]
