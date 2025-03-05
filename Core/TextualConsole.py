from textual.app import App, ComposeResult
from textual.widgets import Static


class TextualConsole(App):
    CSS_PATH = "layout.tcss"

    def compose(self) -> ComposeResult:
        yield Static("Main Chat Window", classes="box", id="large")
        yield Static("Second", classes="box")
        yield Static("Third", classes="box")



    pass

if __name__ == "__main__":
    app = TextualConsole()
    app.run()