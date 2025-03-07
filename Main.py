import os

from Core.Alpacca import Alpacca
from Core.Console import *

if __name__ == '__main__':
    root = os.getcwd()
    name = "phi4"
    alpacca = Alpacca("phi4", history_location=f"{root}/Resources/Chats/{name}.json")

    alpacca.save_alpacca_settings(location=f"{root}/Resources/Settings/{name}.json")

    alpacca.save_history()