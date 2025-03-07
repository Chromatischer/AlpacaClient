import json
import os
from logging import *
from tkinter.constants import NORMAL

from Core.Logger import Logger


def load_from_file(path: str) -> str:
    if not os.path.isfile(path):
        Logger.log(f"File {path} not found.", priority=CRITICAL)
        return ""

    with open(path) as f:
        return f.read().strip()

def load_json(path: str, create: bool = False) -> dict:
    if not os.path.isfile(path):
        Logger.log(f"No json File at {path}!", priority=WARNING)
        if create:
            Logger.log(f"Creating file {path}", priority=NORMAL)
            save_json({}, path)
            Logger.log("Created file!", priority=NORMAL)
            return {}

    with open(path) as f:
        Logger.log(f"Loading file {path}", priority=NORMAL)
        return json.load(f)

def save_json(data: any, path: str):
    Logger.log(f"Saving file {path}", priority=NORMAL)
    # Logger.log(f"Data: {data}", priority=DEBUG)
    if not os.path.exists(os.path.dirname(path)):
        Logger.log(f"Creating directory {os.path.dirname(path)}", priority=NORMAL)
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=4)