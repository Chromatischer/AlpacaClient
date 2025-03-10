from typing import Any

from textual import on
from textual.message import Message


class ExecuteCommand(Message):
    command: str
    args: [Any]

    def __init__(self, command: str, *args):
        self.command = command
        self.args = args
        super().__init__()

    def __str__(self):
        return f"ExecuteCommand({self.command}, {self.args})"

@on(ExecuteCommand)
def on_execute_command(self, message: ExecuteCommand):
    if message.command == "temperature":
        self.log(f"Temperature: {message.args[0]}")