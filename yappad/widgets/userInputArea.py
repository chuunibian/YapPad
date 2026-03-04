from textual.widgets import TextArea
from textual.binding import Binding

'''


## Slide X — Title
---

make that a keybind

--- <- this as well

> Important <- and this


**Questions** <- this as well
- 
---

'''

class UserInputArea(TextArea):

    # !!! Make many keybinds for markdown shortcuts

    BINDINGS = [
        Binding("f1", "insert_slide", "insert slide", show=False),
        Binding("f2", "insert_important", "insert important", show=False),
        Binding("f3", "insert_questions", "insert questions", show=False),
        Binding("f4", "insert_divider", "insert divider", show=False),
        Binding("f5", "insert_table", "insert table", show=False)
    ]

    def action_insert_slide(self) -> None:
        self.insert("## Slide X — Title\n---\n")

    def action_insert_important(self) -> None:
        self.insert("> Important\n")

    def action_insert_questions(self) -> None:
        self.insert("**Questions**\n-\n---\n")

    def action_insert_divider(self) -> None:
        self.insert("---\n")

    def action_insert_table(self) -> None:
        self.insert("| Header 1 | Header 2 | Header 3 |\n|---|---|---|\n|  |  |  |\n")

    BORDER_TITLE = "Input"


