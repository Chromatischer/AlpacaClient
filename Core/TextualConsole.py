import asyncio
import threading
from typing import Coroutine, AsyncIterator, Any, Iterator

from ollama import GenerateResponse
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Center
from textual.reactive import reactive
from textual.widgets import Static, Button, Input, Log
from textual.worker import get_current_worker

from Core.Alpacca import Alpacca

text = "Test text \n\n\n text Test\n"

alpaca = Alpacca(model="phi4")

class Ai_Chat(Static):
    content = reactive("content", repaint=True)
    log: Log = None
    generation: GenerateResponse | Iterator[GenerateResponse] = None

    def __init__(self, log):
        self.update_timer = None
        self.log = log
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(f"{self.content}", classes="body")

    def on_mount(self) -> None:
        self.log.write("Mounting Ai_Chat")
        # asyncio.create_task(self.update_loop())
        self.log.write("Bottom 10 moments...")

    def on_load(self) -> None:
        self.log.write("Load Complete")

    async def update_loop(self):
        print("Update Loop")
        self.log.write("Update Loop Complete")
        if self.generation:
            for response in self.generation:
                self.content = response["response"]
                self.log.write(response.text)
                await asyncio.sleep(1)


class TextualConsole(App):
    CSS_PATH = "layout.tcss"
    style_logger = Log()
    chat = Ai_Chat(style_logger)

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            with Container(id="main-window"):
                with VerticalScroll(id="vertical-scroll-content"):
                    yield self.chat
                with Container(id="side-by-side"):
                    yield Input(placeholder="Chat with AI: ", type="text", tooltip="Type your message here")
                    yield Button("Send")
            with Container(id="side-window"):
                yield Static("Second", classes="debug")
                yield self.style_logger
                #yield Static("Third", classes="debug")

    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line("Mount Complete!")
        self.chat.generation = alpaca.generate_iterable("Hello World!")
        log.write_line("Started the Alpacca")
        # self.ai_content = "Hello World!"


if __name__ == "__main__":
    app = TextualConsole()
    app.run()