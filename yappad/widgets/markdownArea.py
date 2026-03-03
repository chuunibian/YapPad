# from textual.widgets import RichLog


# class MasterMarkdown(RichLog):

#     BORDER_TITLE = "Master Markdown"


from textual.widgets import Markdown

class MasterMarkdown(Markdown):

    BORDER_TITLE = "Preview"
    can_focus = True