# from textual.widgets import RichLog


# class MasterMarkdown(RichLog):

#     BORDER_TITLE = "Master Markdown"


from textual.widgets import MarkdownViewer


class MasterMarkdown(MarkdownViewer):
    BORDER_TITLE = "Preview"
    can_focus = True
