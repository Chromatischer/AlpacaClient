import time
from math import floor
from random import random
from typing import Iterator, List, Any
import psutil

import ollama
from ollama import GenerateResponse
from textual import work
from textual.containers import VerticalScroll
from textual.reactive import reactive, Reactive
from textual.widgets import Static, Input, Log, Tabs, Select, Tab
from textual_plot import PlotWidget

from Core.Alpacca import Alpacca, separate_thoughts, load_alpacca_from_json, RemoteException
from Core.FileTree import *
from Core.Logger import Logger
from Core.MemGraph import Memgraph


class UserMessage(Message):
    user: str

    def __init__(self, user: str):
        self.user = user
        super().__init__()


class AIResponse(Message):
    response: str
    identifier: str

    def __init__(self, value: str, identifier: str):
        self.response = value
        self.identifier = identifier
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
        return f"You: {self.user}\n\nAlpacca: {self.response}\n"


class AiChat(Static):
    lines: Reactive[ChatMessage] = reactive(list, recompose=True)
    _load_from: Alpacca = None
    current_line: ChatMessage = None
    log: Log = None
    generation: GenerateResponse | Iterator[GenerateResponse] = None
    identifier: str = ""

    def __init__(self, log, identifier: str = "Def", load_from: Alpacca = None):
        self.update_timer = None
        self.log = log
        self.identifier = identifier
        self._load_from = load_from
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.current_line is None and len(self.lines) == 0:
            yield Markdown(f"Chat with AI: {self.identifier}")
        else:
            # self.log.write_line(str(self.current_line))
            content = "\n".join(str(m) for m in self.lines)
            # self.log.write_line(content)
            content += "\n" + str(self.current_line)
            yield Markdown(f"{content}")

    def on_mount(self):
        if self._load_from is not None:
            self.load_from_alpacca(self._load_from)

    def new_line(self, user: str):
        """
        Start a new chat exchange between the user and the AI
        :param user: The user input prompt that started the chat exchange
        """
        self.log.write_line(f"New Line Triggered!")

        if self.current_line is not None:
            self.log.write_line(f"Saving old line and adding it to the alpaca's history!")
            self.log.write_line(f"Old Response: {self.current_line.response}")
            self.lines.append(self.current_line)
            self.log.write_line(f"Added old line to the chat history!")

        self.current_line = ChatMessage(user)
        self.log.write_line(f"current_line now reset!")

    def change_happened(self):
        #self.mutate_reactive(AiChat.lines)
        self.query_one(Markdown).update(f"{'\n'.join(str(m) for m in self.lines)}\n{self.current_line}")
        #self.scroll_end(force=True)

    @on(AIResponse)
    def on_ai_response(self, message: AIResponse):
        """
        Handle an AI response
        :param message: The AI response part that was generated
        """
        # self.log.write_line(f"AI Response: {message.response} To: {message.identifier} Self: {self.identifier}")

        if message.identifier.upper() == self.identifier.upper():
            self.current_line.add_part(message.response)
            self.change_happened()

    @on(UserMessage)
    def on_user_message(self, message: UserMessage):
        """
        Handle a user message
        :param message: The user message
        """
        self.log.write_line(f"User message: {message.user} post received!")
        self.new_line(message.user)
        self.change_happened()

    def load_from_alpacca(self, alpacca: Alpacca):
        """
        Load the chat history from an alpacca
        :param alpacca: The alpacca to load the history from
        """
        for exchange in alpacca.get_history():
            message = ChatMessage(exchange.user)
            message.add_part(f"{exchange.thoughts}\n{exchange.answer}")
            self.lines.append(message)


class CreateModelMessage(Message):
    def __init__(self, model: str):
        self.model = model
        super().__init__()


class CreateModelCanceled(Message):
    pass


class ModelSelectScreen(Screen):
    available: List[str] = []

    def __init__(self, logger: Log):
        for model in ollama.list().models:
            self.available.append(model.model)
            logger.write_line(model.model)

        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="side-by-side"):
            yield Button("Cancel", id="cancel-button", classes="select-button")
            yield Select.from_values(self.available)
            yield Button("Select", id="select-button", disabled=True)

    @on(Select.Changed)
    def on_select(self, event: Select.Changed):
        self.get_widget_by_id("select-button").disabled = event.value is Select.BLANK

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel-button":
            self.app.post_message(CreateModelCanceled())
            self.app.pop_screen()
        elif event.button.id == "select-button":
            self.app.post_message(CreateModelMessage(self.query_one(Select).value))
            self.app.pop_screen()


class MainTabs(Tabs):
    TABS = ["Chats", "Settings", "More"]
    logger: Log
    previous_static: Any

    def __init__(self, logger: Log):
        self.logger = logger
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Tabs(id="main-tabs")

    def on_mount(self) -> None:
        self.collect_previous()
        for tab in self.TABS:
            self.query_one(Tabs).add_tab(Tab(tab))

    def collect_previous(self):
        widget = self.app.get_widget_by_id("main-container").children[0]
        if not widget.has_class("Main-Windows"):
            raise TypeError(f"Expected Main-Windows, got {widget.classes} instead")
        self.previous_static = widget

    def replace_main_window(self, new_static: Static) -> None:
        self.app.get_widget_by_id("main-window").remove_children("*")
        self.app.get_widget_by_id("main-window").mount(new_static)

    @on(Tabs.TabMessage)
    def on_tab_activated(self, event: Tabs.TabMessage):
        #self.app.query_one(Log).write_line(str(event.tabs.id))
        if event.tab.label == "Chats":
            self.logger.write_line("Selected Chats!")
            self.collect_previous()
            self.logger.write_line(self.previous_static.id)
        elif event.tab.label == "Settings":
            self.logger.write_line("Selected Settings!")
            self.collect_previous()
            self.logger.write_line(self.previous_static.id)
        elif event.tab.label == "More":
            self.logger.write_line("Selected More!")
            self.collect_previous()
            self.logger.write_line(self.previous_static.id)

        event.stop()  # Stops the following event listeners from receiving the event


class ChatTabs(Tabs):
    log: Log = None
    files: List[str] = []
    alpacas: List[Alpacca] = []

    def __init__(self, logger: Log, alpacas: List[Alpacca], files: List[str], id: str = ""):
        self.log = logger
        self.files = files
        self.alpacas = alpacas
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Tabs(Tab(self.alpacas[0].identifier, id=f"tab-0"))

    def on_mount(self):
        for i in range(1, len(self.alpacas)):
            self.query_one(Tabs).add_tab(Tab(self.alpacas[i].identifier, id=f"tab-{i}"))
        self.query_one(Tabs).add_tab(Tab("+", id="add-tab"))


class SettingsWindow(Static):

    def __init__(self, logger: Log, alpacas: List[Alpacca]):
        self.logger = logger
        self.alpacas = alpacas
        super().__init__(classes="Main-Windows")

    def compose(self) -> ComposeResult:
        yield Placeholder()


class MainWindow(Static):
    logger: Log

    def __init__(self, logger: Log, alpacas: List[Alpacca], files: List[str], chats: List[AiChat]):
        self.logger = logger
        self.alpacas = alpacas
        self.files = files
        self.chats = chats
        super().__init__(id="main-window", classes="Main-Windows")

    def compose(self) -> ComposeResult:
        yield ChatTabs(self.logger, self.alpacas, self.files, id="chat-tabs")
        # yield Tabs("Hello")
        with VerticalScroll(id="vertical-scroll-content"):
            yield self.chats[0]
        with Container(id="side-by-side"):
            yield Button("+", id="button-add")
            yield Input(placeholder="Chat with AI: ", type="text", id="chat-input")
            yield Button("Send", id="send-button")


class TextualConsole(App):
    CSS_PATH = "Core/layout.tcss"
    style_logger = Log()
    chat = AiChat(style_logger)
    std_loc: str = "/Resources/Chats"
    std_settings: str = "/Resources/Settings"
    alpacas: List[Alpacca] = []
    chats: List[AiChat] = []
    files: List[str] = []
    selected_alpaca_id: int = 0
    file_tree_open: bool = False
    generate_running: reactive[bool] = reactive(False)
    main_window: MainWindow
    settings_window: SettingsWindow


    def __init__(self):
        print("Initializing Textual Console")
        self.alpacas, self.files = self.load_alpacca_models()

        if len(self.alpacas) == 0:
            print("No alpacas found: Creating default alpacca")
            self.alpacas.append(self.create_default_alpacca())

        for alpaca in self.alpacas:
            self.chats.append(AiChat(log=self.style_logger, identifier=alpaca.identifier, load_from=alpaca))

        super().__init__()

    def compose(self) -> ComposeResult:
        yield MainTabs(self.style_logger)
        with Container(id="app-grid"):
            with Container(id="main-container"):
                yield MainWindow(logger=self.style_logger, alpacas=self.alpacas, files=self.files, chats=self.chats)
            with Container(id="side-window"):
                yield Memgraph()
                #yield Static("Second", classes="debug")
                yield self.style_logger
                #yield Static("Third", classes="debug")

    def on_mount(self) -> None:
        self.style_logger.write_line("Mount Complete!")
        for name in os.listdir(os.getcwd() + self.std_settings):
            if os.path.isfile(os.getcwd() + self.std_settings + "/" + name):
                self.style_logger.write_line(f"default/{self.std_settings}/{name}")
        self.set_interval(1, self.update_sys_info)

    def update_sys_info(self):
        mem = psutil.virtual_memory()[3] / 1_000_000_000  # in GB
        swap = psutil.swap_memory()[1] / 1_000_000_000
        if self.screen.id == "_default":
            self.app.query_one(Memgraph).append_data_point(time.time(), mem, swap)

    @on(Tabs.TabMessage)
    def on_tab_activated(self, event: Tabs.TabActivated):
        # self.style_logger.write_line(f"Tab Activated! {event.tab.id}")
        if event.tab.id == "add-tab":
            self.style_logger.write_line(f"Add was pressed!")
            self.app.push_screen(ModelSelectScreen(self.style_logger))
        else:
            self.selected_alpaca_id = int(event.tab.id.split("-")[1])
            self.style_logger.write_line(f"Selected alpaca ID: {self.selected_alpaca_id}")
            try:
                self.query_one(AiChat).remove()
            except Exception as e:
                self.style_logger.write_line(f"Error: {e}")

            try:
                self.style_logger.write_line(f"Chat history {self.chats[self.selected_alpaca_id].name}")
                self.query_one(VerticalScroll).mount(self.chats[self.selected_alpaca_id])
                self.recompose()
            except Exception as e:
                self.style_logger.write_line(f"Error: {e}")

    @on(CreateModelCanceled)
    def on_model_canceled(self):
        self.style_logger.write_line("Model creation canceled!")
        self.app.query_one(ChatTabs).action_previous_tab()
        #TODO: Send Tab.Change message to the ChatHistory widget because it is not updating the currently active tab!

    @on(CreateModelMessage)
    def on_create_model(self, event: CreateModelMessage):
        model_str = make_to_model_str(event.model)
        self.alpacas.append(Alpacca(event.model, history_location=f"{os.getcwd() + self.std_loc}/{model_str}.json",
                                    identifier=f"{model_str}"))
        self.chats.append(AiChat(log=self.style_logger, identifier=f"{model_str}"))
        self.query_one(ChatTabs).add_tab(Tab(f"{model_str}", id=f"tab-{len(self.chats) - 1}"), before="add-tab")
        self.recompose()
        self.query_one(ChatTabs).action_previous_tab()

    def create_default_alpacca(self):
        available = ollama.list()
        identifier = make_to_model_str(available.models[0].model)
        return Alpacca(available.models[0].model, identifier=identifier,
                       history_location=f"{os.getcwd() + self.std_loc}/{identifier}.json")

    def load_alpacca_models(self) -> [List[Alpacca], List[str]]:
        """
        Load the alpacca models from the resources folder
        :return: A list of alpacca models and a list of the files that were loaded
        """
        history_files = []
        for name in os.listdir(os.getcwd() + self.std_loc):
            if os.path.isfile(os.getcwd() + self.std_loc + "/" + name):
                history_files.append(name)

        setting_files = []
        for name in os.listdir(os.getcwd() + self.std_settings):
            if os.path.isfile(os.getcwd() + self.std_settings + "/" + name):
                setting_files.append(name)

        for file in history_files:
            print(f"Found history: {file}")

        for file in setting_files:
            print(f"Found setting: {file}")

        alpacas = []
        # only return models that have a setting file, history files are auto generated by the Alpacca class
        for file in setting_files:
            if file.split(".")[1] == "json":
                Logger.log(f"Loading Alpacca: {file}")
                try:
                    alp = load_alpacca_from_json(f"{os.getcwd() + self.std_settings}/{file}")
                    alpacas.append(alp)
                except RemoteException as e:
                    Logger.log(f"Error: {e}")
                    print(f"Error: {e}")

        for alp in alpacas:
            print(f"Loaded Alpacca: {alp}")

        return alpacas, setting_files

    def save_chat(self, chat: AiChat):
        if chat.current_line is not None:
            separated = separate_thoughts(chat.current_line.response)
            self.alpacas[self.selected_alpaca_id].add_history(chat.current_line.user, separated["think"],
                                                              separated["response"])
            self.style_logger.write_line(
                f"In generate_ai: {chat.current_line.user} {separated['think']} {separated['response']}")
            self.style_logger.write_line(f"Saved history for {self.alpacas[self.selected_alpaca_id].identifier}")
        else:
            self.style_logger.write_line(f"Skipping save history because current_line is not yet set!")

    def _on_exit_app(self) -> None:
        for i in range(len(self.chats)):
            chat = self.chats[i]
            self.save_chat(chat)

        for alpaca in self.alpacas:
            alpaca.save_history()
            alpaca.save_alpacca_settings(f"{os.getcwd()}/{self.std_settings}/{alpaca.identifier}.json")
        print(f"Saved history!")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send-button":
            if not self.query_one(Input).value == "":
                self.generate_ai(self.query_one(Input).value)
                #self.chats[self.selected_alpaca_id].post_message(UserMessage(self.query_one(Input).value))
                self.query_one(Input).clear()

        if event.button.id == "button-add":
            if not self.file_tree_open:
                self.app.get_widget_by_id("main-container").mount(FileTee(os.getcwd()))
            else:
                self.app.get_widget_by_id("main-container").query_one(FileTee).remove()
            self.file_tree_open = not self.file_tree_open
            self.app.recompose()

    def on_input_submitted(self, event: Input.Submitted):
        # self.style_logger.write_line("Input Submitted: " + event.value)
        if not (event.value == "" or self.generate_running):
            self.generate_ai(event.value)
            #self.chats[self.selected_alpaca_id].post_message(UserMessage(event.value))
            self.query_one(Input).clear()
            # self.recompose()

    @work(thread=True)
    def generate_ai(self, prompt):
        self.style_logger.write_line(f"Generating Prompt: {prompt}")
        self.generate_running = True
        self.get_widget_by_id("send-button").disabled = True
        chat = self.chats[self.selected_alpaca_id]
        self.save_chat(chat)

        self.chats[self.selected_alpaca_id].post_message(UserMessage(prompt))
        self.style_logger.write_line(f"Message posted!")

        for part in self.alpacas[self.selected_alpaca_id].generate_iterable(prompt=prompt):
            chat.post_message(AIResponse(part["response"], self.alpacas[self.selected_alpaca_id].identifier.upper()))
            self.app.query_one(VerticalScroll).scroll_end(force=True)
            # TODO: Fix the scrolling issue
        self.generate_running = False
        self.get_widget_by_id("send-button").disabled = False


def make_to_model_str(model: str) -> str:
    return model.replace(".", "_").split(":")[0].replace("/", "_").upper() + str(floor(random() * 99))


if __name__ == "__main__":
    app = TextualConsole()
    app.run()
