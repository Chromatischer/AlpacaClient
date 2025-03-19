from math import floor
from random import random

import ollama
import requests
from ollama import Client

from Core.Logger import Logger
from Core.Priority import Priority


def check_ollama_server(host: str = None) -> bool:
    """
    Check if the ollama server is running on the given host or the default host if None is specified
    :param host: The host to check
    :return: True if the server is running, False otherwise
    """
    try:
        if host is not None:
            response = requests.get(f"http://{host}", timeout=5)
            Logger.log(f"Response: {response}", Priority.NORMAL)
            Logger.log(f"Response: {response.text}", Priority.NORMAL)
        else:
            response = requests.get("0.0.0.0:11434", timeout=5)
    except Exception as e:
        Logger.log(f"Exception: {e}", Priority.NORMAL)
        return False
    return response.text.strip().upper() == "OLLAMA IS RUNNING"

def get_model_names_from_remote(host: str) -> list[str]:
    """
    Get the model names that a remote host hosts
    :param host: The host to get the models from
    :return: The models names that are available on the remote host
    """
    if not check_ollama_server(host): raise ValueError("The ollama server is not running on the host")
    return [m["model"] for m in Client(host=host).list().models]

def get_all_models(host:str = None) -> list[str]:
    """
    Get all models from the local and remote ollama servers
    :param host: The host to get the models from or None to get only the local models
    :return: The models names that are available on the combination of the local and remote hosts
    """
    local: list[str] = [m["model"] for m in ollama.list().models]
    if host is None: return local
    remote: list[str] = get_model_names_from_remote(host)
    return local + remote

def make_to_model_str(model: str) -> str:
    return model.replace(".", "_").split(":")[0].replace("/", "_").upper() + str(floor(random() * 99))
