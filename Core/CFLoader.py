import json
import sys
from typing import Any

class CFLoader:
    initialized: bool = False
    file_path: str = "config.json"
    configs: dict[str, Any] = {}

    def __init__(self, file_path: str):
        if CFLoader.initialized:
            print("CFLoader already initialized")
            return
        CFLoader.initialized = True
        CFLoader.file_path = file_path
        CFLoader.__load()
        CFLoader.__from_argv()
        print("CFLoader initialized")

    @staticmethod
    def __load():
        """
        Load the config file
        """
        try:
            with open(CFLoader.file_path, "r") as file:
                CFLoader.configs = json.load(file)
        except FileNotFoundError:
            print(f"Config file not found: {CFLoader.file_path}")

    @staticmethod
    def get_config(key: str) -> Any:
        """
        Get a config value
        :param key: The key of the config value
        :return: The config value
        """
        return CFLoader.configs.get(key)

    @staticmethod
    def set_config(key: str, value: Any):
        """
        Set a config value
        :param key: The key of the config value
        :param value: The value to set
        """
        CFLoader.configs[key] = value
        CFLoader.__save()

    @staticmethod
    def __save():
        """
        Save the config file
        """
        try:
            with open(CFLoader.file_path, "w") as file:
                json.dump(CFLoader.configs, file)
        except Exception as e:
            print(f"Failed to save config file: {e}")

    @staticmethod
    def __from_argv():
        """
        Load config from argv arguments in the form
        key=value
        key2 = value2
        KEY3 = VALUE3
        """
        for arg in sys.argv[1:]:
            key, value = arg.split("=")
            CFLoader.configs[key.strip().lower()] = value.strip().lower()
        CFLoader.__save()
