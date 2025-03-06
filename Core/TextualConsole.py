import asyncio
import threading
from typing import Coroutine, AsyncIterator, Any, Iterator, List

from ollama import GenerateResponse
from textual import work, on
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Center
from textual.message import Message
from textual.reactive import reactive, Reactive
from textual.widgets import Static, Button, Input, Log, Markdown
from textual.worker import get_current_worker

from Core.Alpacca import Alpacca, separate_thoughts

text = "Test text \n\n\n text Test\n"

alpaca = Alpacca(model="phi4", history_location="history.json")

class UserMessage(Message):
    user: str

    def __init__(self, user: str):
        self.user = user
        super().__init__()

class AIResponse(Message):
    response: str

    def __init__(self, value: str):
        self.response = value
        super().__init__()


class ChatMessage(Message):
    user: str
    response: str

    def __init__(self, user: str):
        self.user = user
        self.response = ""
        super().__init__()

    def add_part(self, part: str):
        self.response += part

    def __str__(self):
        return f"You: {self.user}\n\nAlpacca: {self.response}"

class AiChat(Static):
    lines: Reactive[ChatMessage] = reactive(list, recompose=True)
    current_line: ChatMessage = None
    log: Log = None
    generation: GenerateResponse | Iterator[GenerateResponse] = None

    def __init__(self, log):
        self.update_timer = None
        self.log = log
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.current_line is None:
            yield Markdown("Chat with AI", classes="body")
        else:
            # self.log.write_line(str(self.current_line))
            content = "\n".join(str(m) for m in self.lines)
            # self.log.write_line(content)
            content += "\n" + str(self.current_line)
            yield Markdown(f"{content}", classes="body")

    def on_mount(self):
        pass

    def new_line(self, user: str):
        """
        Start a new chat exchange between the user and the AI
        :param user: The user input prompt that started the chat exchange
        """
        self.log.write_line(f"New Chat exchange with user: {user} scheduled!")
        if self.current_line is not None:
            self.lines.append(self.current_line)
            self.log.write_line("Old line: " + str(self.current_line.user) + " saved")
        self.current_line = ChatMessage(user)

    def change_happened(self):
        self.mutate_reactive(AiChat.lines)

    @on(AIResponse)
    def on_ai_response(self, message: AIResponse):
        """
        Handle an AI response
        :param message: The AI response part that was generated
        """
        # self.log.write_line("AI Response: " + message.response)
        self.current_line.add_part(message.response)
        self.change_happened()

    @on(UserMessage)
    def on_user_message(self, message: UserMessage):
        """
        Handle a user message
        :param message: The user message
        """
        self.log.write_line("User message: " + message.user)
        self.new_line(message.user)
        self.change_happened()

class TextualConsole(App):
    CSS_PATH = "layout.tcss"
    style_logger = Log()
    chat = AiChat(style_logger)

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            with Container(id="main-window"):
                with VerticalScroll(id="vertical-scroll-content"):
                    yield self.chat
                with Container(id="side-by-side"):
                    yield Button("+", id="button-add", disabled=True)
                    yield Input(placeholder="Chat with AI: ", type="text", tooltip="Type your message here", id="chat-input")
                    yield Button("Send", id="send-button")
            with Container(id="side-window"):
                yield Static("Second", classes="debug")
                yield self.style_logger
                #yield Static("Third", classes="debug")

    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line("Mount Complete!")
        log.write_line("Started the Alpacca")
        # self.ai_content = "Hello World!"

    def _on_exit_app(self) -> None:
        alpaca.save_history()
        self.style_logger.write_line("Alpacca: Saved Chat history!")
        print(f"Saved history!")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send-button":
            self.generate_ai(self.query_one(Input).value)
            self.chat.post_message(UserMessage(self.query_one(Input).value))
            self.query_one(Input).clear()

    def on_input_submitted(self, event: Input.Submitted):
        self.style_logger.write_line("Input Submitted: " + event.value)
        self.generate_ai(event.value)
        self.chat.post_message(UserMessage(event.value))
        self.query_one(Input).clear()
        # self.recompose()

    @work(thread=True)
    def generate_ai(self, prompt):
        self.style_logger.write_line(f"Generating AI: {prompt}")
        if self.chat.current_line is not None:
            self.style_logger.write_line(f"Saving old line and adding it to the alpacca's history!")
            separated = separate_thoughts(self.chat.current_line.response)
            self.style_logger.write_line(f"Old line: {self.chat.current_line}")
            alpaca.add_history(self.chat.current_line.user, separated["think"], separated["response"])
            self.style_logger.write_line(f"Added old line to the alpacca history!")

        for part in alpaca.generate_iterable(prompt):
            # print(part)
            # print(str(part["response"]))
            self.chat.post_message(AIResponse(part["response"]))

if __name__ == "__main__":
    app = TextualConsole()
    app.run()