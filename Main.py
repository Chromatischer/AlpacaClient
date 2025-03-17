import os

import ollama

import TextualConsole
from Core.Alpacca import Alpacca

if __name__ == '__main__':
    root = os.getcwd()
    model = "gemma3:12b-it-q4_K_M"
    name = TextualConsole.make_to_model_str(model) + "TP"
    alpacca = Alpacca(model=model, history_location=f"{root}/Resources/Chats/{name}.json", identifier=name, system="/Users/chromatischer/PycharmProjects/AI-Assist/Resources/SystemPrompts/DeepResearch.md",
                      host="192.168.178.47:11434")

    alpacca.save_alpacca_settings(location=f"{root}/Resources/Settings/{name}.json")

    alpacca.save_history()

    #for model in ollama.list():
    #    print(model)