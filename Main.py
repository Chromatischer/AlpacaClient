import os

import ollama

import TextualConsole
from Core.Alpacca import Alpacca
from Core.Console import *

if __name__ == '__main__':
    root = os.getcwd()
    model = "phi4"
    name = TextualConsole.make_to_model_str(model) + "TP"
    alpacca = Alpacca(model=model, history_location=f"{root}/Resources/Chats/{name}.json", identifier=name, system="/Users/chromatischer/PycharmProjects/AI-Assist/Resources/SystemPrompts/DeepResearch.md")

    alpacca.save_alpacca_settings(location=f"{root}/Resources/Settings/{name}.json")

    alpacca.save_history()

    #for model in ollama.list():
    #    print(model)