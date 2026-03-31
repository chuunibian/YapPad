from textual.app import ComposeResult
from textual.containers import Center
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Label
from textual.binding import Binding
from textual.errors import NoWidget

from dataclasses import dataclass, field


@dataclass
class JumpTarget:
    """A panel that can be jumped to via the overlay.
    Can also carry a row of associated action keybinds shown along its border.
    """

    key: str  # single character hotkey to focus this panel
    label: str  # human-readable panel name (e.g. "Input", "Preview")
    widget_id: str  # CSS id of the target widget (without #)
    actions: list["QuickAction"] = field(default_factory=list)


@dataclass
class QuickAction:
    """A global action entry in the quick-action palette."""

    key: str  # single character hotkey displayed to user
    label: str  # human-readable description
    action_id: str  # identifier returned on selection


class QuickActionOverlay(ModalScreen[tuple[str, str] | None]):
    """
    Posting-style jump overlay.

    The underlying screen content remains fully visible.
    Small key badges sit on the top border of each panel.
    Each panel also shows its associated action key bindings as a row of badges.
    Two instruction bars sit at the very bottom.

    Returns:
        ("jump", widget_id)   when a panel jump key is pressed
        ("action", action_id) when a global action key is pressed
        None                  when dismissed via ESC / Ctrl+U
    """

    DEFAULT_CSS = """
    QuickActionOverlay {
        background: transparent;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_overlay", "Close", show=False),
        Binding("ctrl+u", "dismiss_overlay", "Close", show=False),
    ]

    def __init__(
        self,
        jump_targets: list[JumpTarget],
        actions: list[QuickAction],
    ) -> None:
        super().__init__()
        self.jump_targets = jump_targets
        self.actions = actions
        # build lookups
        self._jump_key_map: dict[str, str] = {
            t.key.lower(): t.widget_id for t in jump_targets
        }
        self._action_key_map: dict[str, str] = {
            a.key.lower(): a.action_id for a in actions
        }
        # also include per-panel actions in the action map
        for t in jump_targets:
            for a in t.actions:
                self._action_key_map[a.key.lower()] = a.action_id

    def compose(self) -> ComposeResult:
        calling_screen = (
            self.app.screen_stack[-2] if len(self.app.screen_stack) >= 2 else None
        )

        # ── per-panel badges: jump key + action key row ──
        for target in self.jump_targets:
            yield from self._make_panel_badges(target, calling_screen)

        # ── global action row (not attached to any panel) ──
        if self.actions:
            yield from self._make_global_action_row(calling_screen)

        # ── bottom instruction bars ──
        with Center(id="jump-info-bar"):
            yield Label("Press a key to jump")
        with Center(id="jump-dismiss-bar"):
            yield Label("ESC to dismiss")

    # ── helpers ──

    def _make_panel_badges(
        self,
        target: JumpTarget,
        calling_screen,
    ):
        """Yield the panel jump badge + a row of action badges for that panel."""
        if calling_screen is None:
            return

        try:
            widget = calling_screen.query_one(f"#{target.widget_id}", Widget)
        except Exception:
            return

        try:
            wx, wy = calling_screen.get_offset(widget)
        except (NoWidget, Exception):
            return

        # Build the combined badge row: [jump_key] [action_key label] [action_key label] ...
        # Position it at the top border of the panel
        badge_x = wx + 1
        badge_y = wy

        # If the panel has associated actions, render them as a row
        if target.actions:
            parts = []
            # First: the panel jump key
            parts.append(f"[bold #C45AFF]{target.key.lower()}[/]")
            # Then: each action as "key  label"
            for action in target.actions:
                parts.append(f"  [bold #C45AFF]{action.key.lower()}[/]")
                parts.append(f"  [dim]{action.label}[/]")

            row_label = Label(
                " " + " ".join(parts) + " ",
                classes="jump-badge-row",
            )
        else:
            # Just the single jump key badge
            row_label = Label(
                f" [bold]{target.key.lower()}[/] ",
                classes="jump-badge",
            )

        row_label.styles.margin = (badge_y, 0, 0, badge_x)
        yield row_label

    def _make_global_action_row(self, calling_screen):
        """Yield a row of global actions (mode switches, save, open, etc.)
        positioned at the top of the screen."""
        parts = []
        for action in self.actions:
            parts.append(f"[bold #C45AFF]{action.key}[/]")
            parts.append(f"  [dim]{action.label}[/]")

        row = Label(
            " " + "  ".join(parts) + " ",
            classes="action-badge-row",
        )
        # Position at top of screen
        row.styles.margin = (0, 0, 0, 2)
        yield row

    # ── key handling ──

    def on_key(self, event) -> None:
        pressed = event.character
        if not pressed:
            return

        key = pressed.lower()
        if key in self._jump_key_map:
            event.prevent_default()
            event.stop()
            self.dismiss(("jump", self._jump_key_map[key]))
        elif key in self._action_key_map:
            event.prevent_default()
            event.stop()
            self.dismiss(("action", self._action_key_map[key]))

    def action_dismiss_overlay(self) -> None:
        self.dismiss(None)
