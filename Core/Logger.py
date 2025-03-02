import inspect
import json
from datetime import datetime
from typing import List

from Core.Priority import Priority
import Core
from Core import Colors

class Log:
    message: str
    timestamp: datetime.now()
    priority: Priority = Priority.DEBUG
    sender: str = "NA"

    def __init__(self, message: str, priority: Priority = Priority.DEBUG, sender: str = "NA"):
        self.message = message
        self.timestamp = datetime.now()
        self.priority = priority
        self.sender = sender

    def __str__(self):
        return f"{Colors.light_gray}[{self.timestamp.strftime('%H:%M:%S')}: {self.sender}]:{Colors.reset} {Core.Priority.get_color(self.priority)}{self.message}{Colors.reset}"

    def jsonable(self) -> dict:
        return {
            "message": self.message,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "sender": self.sender
        }

class Logger(object):
    """
    A simple logging system with different priority levels and the ability to save logs to a file as well as beautiful colors
    """
    initialized: bool = False
    logs: List[Log] = []

    def __init__(self):
        if Logger.initialized:
            print("Logger already initialized")
            return
        Logger.initialized = True
        print("Logger initialized")

    @staticmethod
    def log( message: str, priority: Priority = Priority.DEBUG):
        """
        Log a message
        :param message: The message to log
        :param priority: The priority of the message
        """
        caller = inspect.stack()[1][3]
        sender = caller if caller != "<module>" else "NA"
        log = Log(message, priority, sender=sender)
        Logger.logs.append(log)
        print(log)

    @staticmethod
    def get_logs() -> List[Log]:
        """
        :return: A list of all logs
        """
        return Logger.logs

    @staticmethod
    def clear_logs():
        """
        Clear all logs
        """
        Logger.logs = []

    @staticmethod
    def save_logs(file_path: str) -> bool:
        """
        Save logs to a file
        :param file_path: The path to save the logs to
        :return: True if the logs were saved successfully, False otherwise
        :rtype: bool
        :raises: Exception
        """
        try:
            with open(file_path, "w") as file:
                json.dump([log.jsonable() for log in Logger.logs], file)
            Logger.log(f"Logs saved to {file_path}", Priority.NORMAL)
            return True
        except Exception as e:
            Logger.log(f"Failed to save logs to {file_path}: {e}", Priority.CRITICAL)
            return False




def get_logger() -> Logger:
    return Logger()