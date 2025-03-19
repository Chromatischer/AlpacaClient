import os

import ollama

import TextualConsole
from Core.Alpacca import Alpacca

if __name__ == '__main__':
    root = os.getcwd()
    model = "qwq"
    host = "192.168.178.47:11434"
    prompt = root + "/Resources/SystemPrompts/DeepResearch.md"
    name = TextualConsole.make_to_model_str(model) + "HST"
    alpacca = Alpacca(model=model, history_location=f"{root}/Resources/Chats/{name}.json", identifier=name, system=None,
                      host=host)

    alpacca.save_alpacca_settings(location=f"{root}/Resources/Settings/{name}.json")

    alpacca.save_history()

    #for model in ollama.list():
    #    print(model)